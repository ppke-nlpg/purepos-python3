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
from docmodel.containers import Sentence
from docmodel.token import Token, ModToken
from purepos.common import util
from purepos.common.analysisqueue import AnalysisQueue
from purepos.common.lemma import batch_convert
from purepos.common.lemmatransformation import def_lemma_representation_by_token
from purepos.model.compiledmodel import CompiledModel, CompiledModelData
from purepos.model.modeldata import ModelData
from purepos.morphology import BaseMorphologicalAnalyser
from purepos.decoder.basedecoder import BeamSearch, BeamedViterbi


class LemmaComparator:
    def __init__(self, compilde_model_data: CompiledModelData, model_data: ModelData):
        self.comp_model_data = compilde_model_data
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
        return self.comp_model_data.combiner.combine(pair[0], pair[1],
                                                     self.comp_model_data, self.model_data)



class POSTagger:
    @staticmethod
    def preprocess_sentence(sentence: list):
        util.analysis_queue.init(len(sentence))
        ret = []
        for i, word in enumerate(sentence):
            if AnalysisQueue.ispreanalysed(word):
                util.analysis_queue.add_word(word, i)
                ret.append(AnalysisQueue.clean(word))
            else:
                ret.append(word)
        return ret

    def __init__(self, model: CompiledModel,
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

    def tag_sentence(self, sentence: list,  # list of strings
                     max_res: int) -> Sentence:
        sentence = self.preprocess_sentence(sentence)
        tag_list = self.decoder.decode(sentence, max_res)
        return [Sentence(self.merge(sentence, tags[0]), score=tags[1]) for tags in tag_list]

    def merge(self, sentence: list, tags: list) -> list:
        vocab = self.model.data.tag_vocabulary
        return [Token(sentence[idx], None, vocab.word(tags[idx]))
                for idx in range(min(len(tags), len(sentence)))]

    def tag(self, source: io.TextIOWrapper, dest: io.TextIOWrapper, max_results_number: int=1):
        for line in source:
            sent_str = self.tag_and_format(line, max_results_number)
            print(sent_str, file=dest)

    def tag_and_format(self, line: str, max_res_num: int) -> str:
        sent_str = ""
        if line.strip() != "":
            s = self.tag_sentence(line.split(), max_res_num)
            sent_str = self.sentences_to_string(s, max_res_num > 1)
        return sent_str

    def sentences_to_string(self, sentences: list, show_prob: bool) -> str:
        return "\t".join([self.sent_to_string(s, show_prob) for s in sentences])

    @staticmethod
    def sent_to_string(sentence: Sentence, show_prob: bool) -> str:
        # ret = " ".join(str(sentence))
        ret = str(sentence)
        if show_prob:
            ret += "$${}$$".format(sentence.score)
        return ret


class MorphTagger(POSTagger):
    def __init__(self, model: CompiledModel,
                 analyser: BaseMorphologicalAnalyser,
                 log_theta: float,
                 suf_theta: float,
                 max_guessed_tags: int,
                 use_beam_search: bool):
        super().__init__(model, analyser, log_theta, suf_theta, max_guessed_tags, use_beam_search)
        self.lemma_comparator = LemmaComparator(model.compiled_data, model.data)
        self.stem_filter = util.StemFilter.create_stem_filter()
        self.is_last_guessed = False

    def merge(self, sentence: list, tags: list) -> list:
        res = super().merge(sentence, tags)
        tmp = []
        pos = 0
        for t in res:
            best_stemmed_token = self.find_best_lemma(t, pos)
            best_stemmed_token = Token(best_stemmed_token.token,
                                       self.mark_guessed(best_stemmed_token.stem.replace(" ", "_")),
                                       best_stemmed_token.tag)
            tmp.append(best_stemmed_token)
            pos += 1
        return Sentence(tmp)

    def mark_guessed(self, lemma: str) -> str:
        if self.is_last_guessed and util.CONFIGURATION is not None:
            return util.CONFIGURATION.guessed_lemma_marker + lemma
        else:
            return lemma

    @staticmethod
    def simplify_lemma(tokens: list or set) -> list:
        return [util.simplify_lemma(t) for t in tokens]

    @staticmethod
    def decode_lemma(tok: Token) -> Token:
        if isinstance(tok, ModToken):
            return Token(tok.token, tok.original_stem, tok.tag)
        return tok

    def find_best_lemma(self, t: Token, position: int) -> Token:
        if util.analysis_queue.has_anal(position):
            stems = self.simplify_lemma(util.analysis_queue.analysises(position))
            self.is_last_guessed = False
        else:
            stems = self.analyser.analyse(t.token)
            self.is_last_guessed = False

        tag_log_probs = self.model.compiled_data.lemma_guesser.tag_log_probabilities(t.token)
        lemma_suff_probs = batch_convert(tag_log_probs, t.token, self.model.data.tag_vocabulary)

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
                    traf = def_lemma_representation_by_token(poss_tok, self.model.data)
                comp.append((poss_tok, traf))
                if not use_morph:
                    lower_tok = Token(poss_tok.token, poss_tok.stem.lower(), poss_tok.tag)
                    comp.append((lower_tok, traf))
            best = (max(comp, key=self.lemma_comparator))[0]
        return self.decode_lemma(best)
