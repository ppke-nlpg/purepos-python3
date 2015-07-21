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

from purepos.model.compiledmodeldata import CompiledModelData
from purepos.common.statistics import Statistics
from purepos.model.suffixtree import BaseSuffixTree, HashLemmaTree, HashSuffixTree
from purepos.model.ngrammodel import NGramModel
from purepos.model.lemmaunigrammodel import LemmaUnigramModel


class RawModelData:
    def __init__(self, tagging_order, emission_order):
        self.stat = Statistics()
        self.tag_ngram_model = NGramModel(tagging_order + 1)
        self.std_emission_ngram_model = NGramModel(emission_order + 1)
        self.spec_emission_ngram_model = NGramModel(2)
        self.eos_tag = None
        self.lemma_suffix_tree = HashLemmaTree(100)
        self.lemma_freq_tree = HashSuffixTree(5)
        self.lemma_unigram_model = LemmaUnigramModel()
        self.lower_suffix_tree = HashSuffixTree(0)
        self.upper_suffix_tree = HashSuffixTree(0)
        self.lemma_lambdas = list()
        from purepos.model.combiner import default_combiner
        self.combiner = default_combiner()

    def compile(self) -> CompiledModelData:
        c = CompiledModelData()
        c.unigram_lemma_model = self.lemma_unigram_model
        c.tag_transition_model = self.tag_ngram_model.create_probability_model()
        c.standard_emission_model = self.std_emission_ngram_model.create_probability_model()
        c.spec_tokens_emission_model = self.spec_emission_ngram_model.create_probability_model()
        c.apriori_tag_probs = self.tag_ngram_model.word_apriori_probs()
        theta = BaseSuffixTree.calculate_theta(c.apriori_tag_probs)
        c.lower_case_suffix_guesser = self.lower_suffix_tree.create_guesser(theta)
        c.upper_case_suffix_guesser = self.upper_suffix_tree.create_guesser(theta)
        c.lemma_guesser = self.lemma_suffix_tree.create_guesser(theta)
        c.suffix_lemma_model = self.lemma_freq_tree.create_guesser(theta)
        c.combiner = self.combiner
        return c
