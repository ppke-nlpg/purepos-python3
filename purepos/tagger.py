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
from purepos.decoder.basedecoder import BeamSearch, BeamedViterbi


class LemmaComparator:
    def __init__(self, model_data: Model):
        self.model_data = model_data

    # def compare(self, t1: tuple, t2: tuple):
    #     # Java comparable interfész. E helyett itt callable.
    #     combiner = self.comp_model_data.combiner
    #     final_score1 = combiner.combine(t1[0], t1[1], self.comp_model_data, self.model_data)
    #     final_score2 = combiner.combine(t2[0], t2[1], self.comp_model_data, self.model_data)
    #     if final_score1 == final_score2:
    #         return 0
    #     if final_score1 < final_score2:
    #         return -1
    #     else:
    #         return 1

    def __call__(self, pair):
        return self.model_data.combiner.combine(pair[0], pair[1], self.model_data)


class POSTagger:
    @staticmethod
    def preprocess_sentence(sentence: list):
        analysis_queue.init(len(sentence))
        ret = []
        for i, word in enumerate(sentence):
            if AnalysisQueue.ispreanalysed(word):
                analysis_queue.add_word(word, i)
                ret.append(AnalysisQueue.clean(word))
            else:
                ret.append(word)
        return ret

    def __init__(self, model: Model,
                 analyser: BaseMorphologicalAnalyser,
                 log_theta: float,
                 suf_theta: float,
                 max_guessed_tags: int,
                 use_beam_search: bool):
        self.model = model
        self.analyser = analyser
        if use_beam_search:
            # todo esetleg beam_size a parancssorból?
            self.decoder = BeamSearch(model, analyser, log_theta, suf_theta, max_guessed_tags)
        else:
            self.decoder = BeamedViterbi(model, analyser, log_theta, suf_theta, max_guessed_tags)

    # list of strings
    def tag_sentence(self, sentence: list, max_res: int) -> tuple:
        sentence = self.preprocess_sentence(sentence)
        return [(self.merge(sentence, tags[0]), tags[1]) for tags in self.decoder.decode(sentence, max_res)]

    def merge(self, sentence: list, tags: list) -> list:
        return [Token(sentence[idx], None, self.model.tag_vocabulary.word(tags[idx]))
                for idx in range(min(len(tags), len(sentence)))]

    def tag(self, source: io.TextIOWrapper, dest: io.TextIOWrapper, max_results_number: int=1):
        for line in source:
            print(self.tag_and_format(line, max_results_number), file=dest)

    def tag_and_format(self, line: str, max_res_num: int) -> str:
        sent_str = ''
        line = line.strip().split()
        if len(line) > 0:
            sent_str = '\t'.join(self.sent_to_string(s, max_res_num > 1) for s in self.tag_sentence(line, max_res_num))
        return sent_str

    @staticmethod
    def sent_to_string(sentence: tuple, show_prob: bool) -> str:
        # ret = " ".join(str(sentence))
        ret = str(sentence[0])
        if show_prob:
            ret += "$${}$$".format(sentence[1])
        return ret


class MorphTagger(POSTagger):
    def __init__(self, model: Model,
                 analyser: BaseMorphologicalAnalyser,
                 log_theta: float,
                 suf_theta: float,
                 max_guessed_tags: int,
                 use_beam_search: bool):
        super().__init__(model, analyser, log_theta, suf_theta, max_guessed_tags, use_beam_search)
        self.lemma_comparator = LemmaComparator(model)
        self.stem_filter = util.StemFilter.create_stem_filter()
        self.is_last_guessed = False

    def merge(self, sentence: list, tags: list) -> list:
        tmp = []
        for pos, t in enumerate(Token(sentence[idx], None, self.model.tag_vocabulary.word(tags[idx]))
                                for idx in range(min(len(tags), len(sentence)))):
            best_stemmed_token = self.find_best_lemma(t, pos)
            best_stemmed_token = Token(best_stemmed_token.token,
                                       self.mark_guessed(best_stemmed_token.stem.replace(" ", "_")),
                                       best_stemmed_token.tag)
            tmp.append(best_stemmed_token)
        return tmp

    def mark_guessed(self, lemma: str) -> str:
        if self.is_last_guessed and util.CONFIGURATION is not None:
            return util.CONFIGURATION.guessed_lemma_marker + lemma
        else:
            return lemma

    def find_best_lemma(self, t: Token, position: int) -> Token:
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
            best = (max(comp, key=self.lemma_comparator))[0]

        if isinstance(best, ModToken):
            return Token(best.token, best.original_stem, best.tag)
        return best
