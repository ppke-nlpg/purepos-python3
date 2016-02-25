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
from purepos.common.analysisqueue import AnalysisQueue
from purepos.common.lemmatransformation import LemmaTransformation, batch_convert
from purepos.configuration import Configuration
from purepos.decoder.beamedviterbi import BeamedViterbi
from purepos.model.model import Model
from purepos.morphology import Morphology
from purepos.common.spectokenmatcher import SpecTokenMatcher


class MorphTagger:
    def __init__(self, model: Model, analyser: Morphology, log_theta: float, suf_theta: float,
                 max_guessed_tags: int, beam_size: int, no_stemming: bool, toksep: str, anal_queue: AnalysisQueue,
                 conf: Configuration, spec_token_matcher: SpecTokenMatcher):
        self.model = model
        self.analyser = analyser
        self.decoder = BeamedViterbi(model, analyser, log_theta, suf_theta, max_guessed_tags, spec_token_matcher,
                                     beam_size)
        self.no_stemming = no_stemming
        self.toksep = toksep
        self.find_best_lemma = self._find_best_lemma
        self.analysis_queue = []
        self.analysis_queue_parser = anal_queue
        self.conf = conf
        if not self.no_stemming:
            self.find_best_lemma = lambda x, _: x

    # todo: Ebben a függvényben és a sent_to_string() függvényben kéne a bemeneti formátumot egységesíteni...
    def tag(self, source: io.TextIOWrapper, dest: io.TextIOWrapper, max_results_number: int=1):
        for line in source:
            print('\t'.join(self.sent_to_string(s, (max_results_number > 1))
                            for s in self.tag_sentence(line.strip().split(), max_results_number)), file=dest)

    def sent_to_string(self, sentence: tuple, show_prob: bool) -> str:
        ret = self.toksep.join(str(i) for i in sentence[0])
        if show_prob:
            ret += '$${}$$'.format(sentence[1])  # todo: kivezetni konfigba a formátumot
        return ret

    def tag_sentence(self, sentence: list, max_res: int) -> tuple:
        # Here 'Sentence' type is the input and '[Sentence]' is the output (has nothing to do with input formatting)
        self.analysis_queue = [None for _ in range(len(sentence))]  # Allocate memory for faster filling...
        preped_sent = []
        for i, word in enumerate(sentence):
            if self.analysis_queue_parser.ispreanalysed(word):
                self.analysis_queue[i] = self.analysis_queue_parser.add_word(word, self.model.tag_vocabulary)
                preped_sent.append(self.analysis_queue_parser.clean(word))
            else:
                preped_sent.append(word)
        ret = []
        for tag_list, weight in self.decoder.decode(preped_sent, max_res, self.analysis_queue):
            sent = []
            for idx in range(min(len(tag_list), len(preped_sent))):
                tok = Token(preped_sent[idx], None, self.model.tag_vocabulary.word(tag_list[idx]))
                sent.append(self.find_best_lemma(tok, idx))  # Optionally find best lemma or leave as is ...
            ret.append((sent, weight))  # Every tag combination with the probability for the current sentence

        return ret

    # todo: Ezt végig kéne gondolni, hogy tényleg így a legjobb-e...
    def _find_best_lemma(self, t: Token, position: int) -> Token:
        if self.analysis_queue[position] is not None:
            stems = self.analysis_queue[position].word_anals()
            for t in stems:
                t.simplify_lemma()
        else:
            stems = self.analyser.analyse(t.token)

        # dict: lemma -> (lemmatrans, prob)
        lemma_suff_probs = batch_convert(self.model.lemma_suffix_tree.tag_log_probabilities(t.token), t.token,
                                         self.model.tag_vocabulary)

        guessed = len(stems) == 0
        if guessed:
            stems = lemma_suff_probs.keys()

        possible_stems = [ct for ct in stems if t.tag == ct.tag]

        if len(possible_stems) == 0:
            best = Token(t.token, t.token, t.tag)  # lemma = token
        elif len(possible_stems) == 1 and t.token == t.token.lower():  # If upper then it could be at sentence start...
            best = possible_stems[0]
        else:
            comp = []
            for poss_tok in possible_stems:
                pair = lemma_suff_probs.get(poss_tok)  # (lemmatrans, prob)
                if pair is not None:
                    traf = pair[0]
                else:
                    traf = LemmaTransformation(poss_tok.token, poss_tok.stem,
                                               self.model.tag_vocabulary.index(poss_tok.tag))  # Get
                comp.append((poss_tok, traf))
                if guessed:  # Append lowercased stems...
                    lower_tok = Token(poss_tok.token, poss_tok.stem.lower(), poss_tok.tag)
                    comp.append((lower_tok, traf))
            best = (max(comp, key=lambda p: self.model.combiner.combine(p[0], p[1], self.model)))[0]

        if best.original_stem is not None:
            best.stem = best.original_stem

        lemma = best.stem.replace(' ', '_')
        if guessed and self.conf is not None:
            lemma = self.conf.guessed_lemma_marker + lemma

        return Token(best.token, lemma, best.tag)
