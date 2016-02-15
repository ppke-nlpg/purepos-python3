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
from corpusreader.containers import Token, ModToken
from purepos.common import util
from purepos.common.analysisqueue import AnalysisQueue, analysis_queue
from purepos.common.lemmatransformation import def_lemma_representation_by_token, batch_convert
from purepos.model.model import Model
from purepos.morphology import BaseMorphologicalAnalyser
from purepos.decoder.basedecoder import BeamedViterbi


class MorphTagger:
    def __init__(self, model: Model, analyser: BaseMorphologicalAnalyser,
                 log_theta: float, suf_theta: float, max_guessed_tags: int, use_beam_search: bool, no_stemming: bool):
        self.model = model
        self.analyser = analyser
        self.decoder = BeamedViterbi(model, analyser, log_theta, suf_theta, max_guessed_tags, use_beam_search)
        self.no_stemming = no_stemming
        if not self.no_stemming:
            self.stem_filter = util.StemFilter.create_stem_filter()
            self.is_last_guessed = False

    def tag(self, source: io.TextIOWrapper, dest: io.TextIOWrapper, max_results_number: int=1):
        for line in source:
            print(self.tag_and_format(line, max_results_number), file=dest)

    def tag_and_format(self, line: str, max_res_num: int) -> str:
        writer = lambda x: str(x[0])
        if max_res_num > 1:
            writer = lambda x: '{0}$${1}$$'.format(x[0], x[1])
        return '\t'.join(writer(s) for s in self.tag_sentence(line.strip().split(), max_res_num))

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

        ret = []
        for pos, t in enumerate(tmp):
            best_stemmed_token = self._find_best_lemma(t, pos)
            best_stemmed_token = Token(best_stemmed_token.token,
                                       self._mark_guessed(best_stemmed_token.stem.replace(" ", "_")),
                                       best_stemmed_token.tag)
            ret.append(best_stemmed_token)
        return ret

    def _mark_guessed(self, lemma: str) -> str:
        if self.is_last_guessed and util.CONFIGURATION is not None:
            return util.CONFIGURATION.guessed_lemma_marker + lemma
        else:
            return lemma

    def _find_best_lemma(self, t: Token, position: int) -> Token:
        if analysis_queue.has_anal(position):
            stems = [util.simplify_lemma(t) for t in analysis_queue.analysises(position)]
            self.is_last_guessed = False
        else:
            stems = self.analyser.analyse(t.token)
            self.is_last_guessed = False

        tag_log_probs = self.model.lemma_suffix_tree.tag_log_probabilities(t.token)
        lemma_suff_probs = batch_convert(tag_log_probs, t.token, self.model.tag_vocabulary)

        use_morph = True
        if len(stems) == 0:
            self.is_last_guessed = True
            use_morph = False
            stems = set(lemma_suff_probs.keys())

        possible_stems = [ct for ct in stems if t.tag == ct.tag]

        if len(possible_stems) == 0:
            return Token(t.token, t.token, t.tag)

        if len(possible_stems) == 1 and t.token == t.token.lower():
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
                    traf = def_lemma_representation_by_token(poss_tok, self.model)
                comp.append((poss_tok, traf))
                if not use_morph:
                    lower_tok = Token(poss_tok.token, poss_tok.stem.lower(), poss_tok.tag)
                    comp.append((lower_tok, traf))
            best = (max(comp, key=lambda p: self.model.combiner.combine(p[0], p[1], self.model)))[0]

        if isinstance(best, ModToken):
            return Token(best.token, best.original_stem, best.tag)
        return best
