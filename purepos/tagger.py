#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-
###############################################################################
# Copyright (c) 2015 Móréh, Tamás
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the GNU Lesser Public License v3
# which accompanies this distribution, and is available at
# http://www.gnu.org/licenses/
#
# This file is part of PurePos-Python3.
#
# PurePos-Python3 is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PurePos-Python3 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# Contributors:
#     Móréh, Tamás - initial API and implementation
##############################################################################

__author__ = 'morta@digitus.itk.ppke.hu'

import io
from corpusreader.containers import Token
from purepos.common import util
from purepos.common.analysisqueue import AnalysisQueue, analysis_queue
from purepos.common.lemmatransformation import def_lemma_representation, batch_convert
from purepos.model.model import Model
from purepos.morphology import Morphology
from purepos.decoder.beamedviterbi import BeamedViterbi


class MorphTagger:
    def __init__(self, model: Model, analyser: Morphology, log_theta: float, suf_theta: float,
                 max_guessed_tags: int, beam_size: int, no_stemming: bool, toksep: str):
        self.model = model
        self.analyser = analyser
        self.decoder = BeamedViterbi(model, analyser, log_theta, suf_theta, max_guessed_tags, beam_size)
        self.no_stemming = no_stemming
        self.toksep = toksep
        if not self.no_stemming:
            self.stem_filter = util.StemFilter.create_stem_filter()
            self.is_last_guessed = False

    def tag(self, source: io.TextIOWrapper, dest: io.TextIOWrapper, max_results_number: int=1):
        for line in source:
            print(self.tag_and_format(line, max_results_number), file=dest)

    def tag_and_format(self, line: str, max_res_num: int) -> str:
        return '\t'.join(self.sent_to_string(s, (max_res_num > 1)) for s in self.tag_sentence(line.strip().split(),
                                                                                              max_res_num))

    def sent_to_string(self, sentence: tuple, show_prob: bool) -> str:
        ret = self.toksep.join(str(i) for i in sentence[0])
        if show_prob:
            ret += "$${}$$".format(sentence[1])  # todo: kivezetni konfigba a formátumot
        return ret

    # list of strings
    def tag_sentence(self, sentence: list, max_res: int) -> tuple:
        analysis_queue.init(len(sentence))
        preped_sent = []
        for i, word in enumerate(sentence):
            if AnalysisQueue.ispreanalysed(word):
                analysis_queue.add_word(word, i)
                preped_sent.append(AnalysisQueue.clean(word))
            else:
                preped_sent.append(word)
        return [(self.merge(preped_sent, tags[0]), tags[1]) for tags in self.decoder.decode(preped_sent, max_res)]

    def merge(self, sentence: list, tags: list) -> list:
        tmp = [Token(sentence[idx], None, self.model.tag_vocabulary.word(tags[idx]))
               for idx in range(min(len(tags), len(sentence)))]
        if self.no_stemming:
            return tmp
        return [self._find_best_lemma(t, pos) for pos, t in enumerate(tmp)]

    # todo: ezen van még mit optimalizálni (tényleg mindenhol új tokent kell gyártani?)
    def _find_best_lemma(self, t: Token, position: int) -> Token:
        if analysis_queue.has_anal(position):
            stems = analysis_queue.analysises(position)
            for t in stems:
                t.simplify_lemma()
            self.is_last_guessed = False
        else:
            stems = self.analyser.analyse(t.token)
            self.is_last_guessed = False

        lemma_suff_probs = batch_convert(self.model.lemma_suffix_tree.tag_log_probabilities(t.token), t.token,
                                         self.model.tag_vocabulary)

        use_morph = True
        if len(stems) == 0:
            self.is_last_guessed = True
            use_morph = False
            stems = lemma_suff_probs.keys()

        possible_stems = [ct for ct in stems if t.tag == ct.tag]

        if len(possible_stems) == 0:
            best = Token(t.token, t.token, t.tag)  # todo: Muszáj lemásolni?
        elif len(possible_stems) == 1 and t.token == t.token.lower():
            best = possible_stems[0]
        else:
            if self.stem_filter is not None:
                possible_stems = self.stem_filter.filter_stem(possible_stems)
            comp = []
            for poss_tok in possible_stems:
                pair = lemma_suff_probs.get(poss_tok)
                if pair is not None:
                    traf = pair[0]
                else:
                    traf = def_lemma_representation(poss_tok.token, poss_tok.stem,
                                                    self.model.tag_vocabulary.index(poss_tok.tag))  # Get
                comp.append((poss_tok, traf))
                if not use_morph:
                    lower_tok = Token(poss_tok.token, poss_tok.stem.lower(), poss_tok.tag)
                    comp.append((lower_tok, traf))
            best = (max(comp, key=lambda p: self.model.combiner.combine(p[0], p[1], self.model)))[0]

        if best.original_stem is not None:
            best.stem = best.original_stem

        lemma = best.stem.replace(" ", "_")
        if self.is_last_guessed and util.CONFIGURATION is not None:
            lemma = util.CONFIGURATION.guessed_lemma_marker + lemma

        return Token(best.token, lemma, best.tag)
