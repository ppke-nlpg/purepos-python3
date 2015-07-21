#!/usr/bin/env python3
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

from docmodel.containers import Document
from docmodel.token import Token
from purepos.common import util, lemma
from purepos.model.modeldata import ModelData
from purepos.model.rawmodeldata import RawModelData
from purepos.model.compiledmodeldata import CompiledModelData
from purepos.model.suffixtree import BaseSuffixTree


def default_combiner():
    return LogLinearBiCombiner()


class BaseCombiner:
    def __init__(self):
        self.lambdas = []

    def parameters(self):
        return self.lambdas

    def calculate_params(self, doc: Document,
                         raw_modeldata: RawModelData,
                         modeldata: ModelData):
        pass

    def combine(self, token: Token,
                lem_transf: lemma.BaseLemmaTransformation,
                compiled_modeldata: CompiledModelData,
                modeldata: ModelData) -> float:  # todo: Double... version of func?
        pass


class LogLinearBiCombiner(BaseCombiner):
    def calculate_params(self, doc: Document,
                         raw_modeldata: RawModelData,
                         modeldata: ModelData):
        apriori_probs = raw_modeldata.tag_ngram_model.word_apriori_probs()
        theta = BaseSuffixTree.calculate_theta(apriori_probs)
        lemma_suffix_guesser = raw_modeldata.lemma_suffix_tree.create_guesser(theta)
        lambda_s = 1.0
        lambda_u = 1.0
        for sentence in doc.sentences():
            for tok in sentence:
                suffix_probs = lemma.batch_convert(lemma_suffix_guesser.tag_log_probabilities(
                    tok.token), tok.token, modeldata.tag_vocabulary)
                uni_probs = dict()
                for t in suffix_probs.keys():
                    uniscore = raw_modeldata.lemma_unigram_model.log_prob(t.stem)
                    uni_probs[t] = uniscore
                uni_max = util.find_max(uni_probs)
                suffix_max = util.find_max_pair(suffix_probs)
                act_uni_prob = raw_modeldata.lemma_unigram_model.log_prob(tok.stem)
                # act_suff_prob = float()
                if tok in suffix_probs.keys():
                    act_suff_prob = suffix_probs[tok][1]
                else:
                    act_suff_prob = util.UNKOWN_VALUE
                uni_prop = act_uni_prob - uni_max[1]
                suff_prop = act_suff_prob - suffix_max[1]
                if uni_prop > suff_prop:
                    lambda_u += uni_prop - suff_prop
                elif suff_prop > uni_prop:
                    lambda_s += suff_prop - uni_prop
        s = lambda_u + lambda_s
        lambda_u /= s
        lambda_s /= s
        self.lambdas.append(lambda_u)
        self.lambdas.append(lambda_s)

    def combine(self, token: Token,
                lem_transf: lemma.BaseLemmaTransformation,
                compiled_modeldata: CompiledModelData,
                modeldata: ModelData) -> float:
        unigram_lemma_model = compiled_modeldata.unigram_lemma_model
        uni_score = unigram_lemma_model.log_prob(token.stem)
        suffix_score = util.smooth(
            compiled_modeldata.lemma_guesser.tag_log_probability(token.token, lem_transf))
        uni_lambda = self.lambdas[0]
        suffix_lambda = self.lambdas[1]
        if util.CONFIGURATION is not None and util.CONFIGURATION.weight is not None:
            suffix_lambda = util.CONFIGURATION.weight
            uni_lambda = 1 - suffix_lambda

        return uni_score * uni_lambda + suffix_score * suffix_lambda


class LogLinearMLCombiner(BaseCombiner):
    def calculate_params(self, doc: Document,
                         raw_modeldata: RawModelData,
                         modeldata: ModelData):
        self.lambdas = [0.0, 0.1]

    def combine(self, token: Token,
                lem_transf: lemma.BaseLemmaTransformation,
                compiled_modeldata: CompiledModelData,
                modeldata: ModelData) -> float:
        unigram_lemma_model = compiled_modeldata.unigram_lemma_model
        uni_score = unigram_lemma_model.log_prob(token.stem)
        suffix_score = util.smooth(
            compiled_modeldata.lemma_guesser.tag_log_probability(token.token, lem_transf))
        return uni_score * self.lambdas[0] + suffix_score * self.lambdas[1]


class LogLinearTriCombiner(BaseCombiner):
    def calculate_params(self, doc: Document,
                         raw_modeldata: RawModelData,
                         modeldata: ModelData):
        apriori_probs = raw_modeldata.tag_ngram_model.word_apriori_probs()
        theta = BaseSuffixTree.calculate_theta(apriori_probs)
        lemma_suffix_guesser = raw_modeldata.lemma_suffix_tree.create_guesser(theta)
        lemma_prob = raw_modeldata.lemma_freq_tree.create_guesser(theta)
        lemma_unigram_model = raw_modeldata.lemma_unigram_model
        lambda_s = 1.0
        lambda_u = 1.0
        lambda_l = 1.0
        for sentence in doc.sentences():
            for tok in sentence:
                suffix_probs = lemma.batch_convert(lemma_suffix_guesser.tag_log_probabilities(
                    tok.token), tok.token, modeldata.tag_vocabulary)
                uni_probs = dict()
                for t in suffix_probs.keys():
                    uniscore = lemma_unigram_model.log_prob(t.stem)
                    uni_probs[t] = uniscore
                lemma_probs = dict()
                for t in suffix_probs.keys():
                    lemma_score = lemma_prob.tag_log_probability(t.stem, lemma.main_pos_tag(t.tag))
                    lemma_probs[t] = lemma_score
                uni_max = util.find_max(uni_probs)
                suffix_max = util.find_max_pair(suffix_probs)
                lemma_max = util.find_max(lemma_probs)
                act_uni_prob = lemma_unigram_model.log_prob(tok.stem)
                act_lemma_prob = lemma_prob.tag_log_probability(tok.stem, lemma.main_pos_tag(
                    tok.tag))
                if tok in suffix_probs.keys():
                    act_suff_prob = suffix_probs[tok][1]
                else:
                    act_suff_prob = util.UNKOWN_VALUE
                uni_prop = act_uni_prob - uni_max[1]
                suff_prop = act_suff_prob - suffix_max[1]
                lemma_prop = act_lemma_prob - lemma_max[1]
                if uni_prop > suff_prop and uni_prop > lemma_prop:
                    lambda_u += uni_prop
                elif suff_prop > uni_prop and suff_prop > lemma_prop:
                    lambda_s += suff_prop
                elif lemma_prop > uni_prop and lemma_prop > suff_prop:
                    lambda_l += lemma_prop
        s = lambda_u + lambda_s + lambda_l
        lambda_u /= s
        lambda_s /= s
        lambda_l /= s
        self.lambdas.append(lambda_u)
        self.lambdas.append(lambda_s)
        self.lambdas.append(lambda_l)

    def combine(self, token: Token,
                lem_transf: lemma.BaseLemmaTransformation,
                compiled_modeldata: CompiledModelData,
                modeldata: ModelData) -> float:
        unigram_lemma_model = compiled_modeldata.unigram_lemma_model
        uni_score = unigram_lemma_model.log_prob(token.stem)
        suffix_score = util.smooth(compiled_modeldata.lemma_guesser.tag_log_probability(
            token.token, lem_transf))
        lemma_prob = compiled_modeldata.\
            suffix_lemma_model.tag_log_probability(token.stem, lemma.main_pos_tag(token.tag))
        return uni_score * self.lambdas[0] +\
            suffix_score * self.lambdas[1] +\
            lemma_prob * self.lambdas[2]
