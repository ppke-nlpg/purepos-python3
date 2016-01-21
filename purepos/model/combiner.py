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

from corpusreader.containers import Document, Token
from purepos.common.util import UNKNOWN_VALUE, CONFIGURATION
from purepos.common.lemmatransformation import BaseLemmaTransformation, batch_convert
from purepos.model.model import Model
# from purepos.model.suffixguesser import HashSuffixTree


def default_combiner():
    return LogLinearBiCombiner()


# todo: Do we need base class or just LogLinearBiCombiner?
class BaseCombiner:
    def __init__(self):
        self.lambdas = []

    def parameters(self):  # Unused...
        return self.lambdas

    def calculate_params(self, doc: Document, modeldata: Model):
        pass

    def combine(self, token: Token, lem_transf: BaseLemmaTransformation, modeldata: Model) -> float:
        pass


class LogLinearBiCombiner(BaseCombiner):
    def __init__(self):
        super().__init__()
        self.lambdas = [1.0, 1.0]

    def calculate_params(self, doc: Document, modeldata: Model):
        lambda_u = self.lambdas[0]
        lambda_s = self.lambdas[1]
        for sentence in (sent for para in doc for sent in para):
            for tok in sentence:
                suffix_probs = batch_convert(modeldata.lemma_suffix_tree.tag_log_probabilities(tok.token), tok.token,
                                             modeldata.tag_vocabulary)
                # Tokens mapped to unigram score and the maximal score is selected
                uni_max_prob = max(modeldata.lemma_unigram_model.log_prob(t.stem) for t in suffix_probs.keys())
                # Same with sufixes
                suffix_max_prob = max(prob for _, prob in suffix_probs.values())
                act_uni_prob = modeldata.lemma_unigram_model.log_prob(tok.stem)
                act_suff_prob = suffix_probs.get(tok, (None, UNKNOWN_VALUE))[1]

                uni_prop = act_uni_prob - uni_max_prob
                suff_prop = act_suff_prob - suffix_max_prob
                if uni_prop > suff_prop:
                    lambda_u += uni_prop - suff_prop
                elif suff_prop > uni_prop:
                    lambda_s += suff_prop - uni_prop

        s = lambda_u + lambda_s
        lambda_u /= s
        lambda_s /= s
        # Bug in PurePOS: incremental learning mishandle lambdas (only the first two elements used but others may added)
        self.lambdas[0] = lambda_u
        self.lambdas[1] = lambda_s

    def combine(self, token: Token, lem_transf: BaseLemmaTransformation, modeldata: Model) -> float:
        if CONFIGURATION is not None and CONFIGURATION.weight is not None:
            self.lambdas[0] = CONFIGURATION.weight
            self.lambdas[1] = 1 - CONFIGURATION.weight

        return (self.lambdas[0] * modeldata.lemma_unigram_model.log_prob(token.stem) +
                self.lambdas[1] * modeldata.lemma_suffix_tree.tag_log_probability(token.token, lem_transf))


# Csak a BiCombinert használjuk, ami innen jön, dead code.

"""
class LogLinearMLCombiner(BaseCombiner):
    def calculate_params(self, doc: Document,
                         raw_modeldata: RawModelData,
                         modeldata: ModelData):
        self.lambdas = [0.0, 0.1]

    def combine(self, token: Token, lem_transf: BaseLemmaTransformation, compiled_modeldata: CompiledModelData,
                modeldata: ModelData) -> float:
        return self.lambdas[0] * compiled_modeldata.unigram_lemma_model.log_prob(token.stem) + \
               self.lambdas[1] * compiled_modeldata.lemma_guesser.tag_log_probability(token.token, lem_transf)


class LogLinearTriCombiner(BaseCombiner):
    def calculate_params(self, doc: Document, raw_modeldata: RawModelData, modeldata: ModelData):
        theta = HashSuffixTree.calculate_theta(raw_modeldata.tag_ngram_model.word_apriori_probs())
        lemma_suffix_tag_log_probabilities = raw_modeldata.lemma_suffix_tree.create_guesser(theta).tag_log_probabilities
        lemma_unigram_model_log_prob = raw_modeldata.lemma_unigram_model.log_prob
        lemma_tag_log_probability = raw_modeldata.lemma_freq_tree.create_guesser(theta).tag_log_probability

        lambda_u, lambda_s, lambda_l = 1.0, 1.0, 1.0
        for sentence in doc.sentences():
            for tok in sentence:
                suffix_probs = batch_convert(lemma_suffix_tag_log_probabilities(tok.token), tok.token,
                                             modeldata.tag_vocabulary)
                uni_max_prob = max(lemma_unigram_model_log_prob(t.stem) for t in suffix_probs.keys())
                suffix_max_prob = max(prob for _, prob in suffix_probs.values())
                lemma_max_prob = max(lemma_tag_log_probability(t.stem, main_pos_tag(t.tag))
                                     for t in suffix_probs.keys())

                act_uni_prob = lemma_unigram_model_log_prob(tok.stem)
                act_suff_prob = suffix_probs.get(tok, (None, UNKNOWN_VALUE))[1]
                act_lemma_prob = lemma_tag_log_probability(tok.stem, main_pos_tag(tok.tag))

                uni_prop = act_uni_prob - uni_max_prob
                suff_prop = act_suff_prob - suffix_max_prob
                lemma_prop = act_lemma_prob - lemma_max_prob
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

    def combine(self, token: Token, lem_transf: BaseLemmaTransformation, compiled_modeldata: CompiledModelData,
                modeldata: ModelData) -> float:
        # uni_score + suffix_score + lemma_prob
        return self.lambdas[0] * compiled_modeldata.unigram_lemma_model.log_prob(token.stem) + \
               self.lambdas[1] * compiled_modeldata.lemma_guesser.tag_log_probability(token.token, lem_transf) + \
               self.lambdas[2] * compiled_modeldata.suffix_lemma_model.tag_log_probability(token.stem,
                                                                                           main_pos_tag(token.tag))
"""
