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

from purepos.model.vocabulary import BaseVocabulary, IntVocabulary
from purepos.model.lexicon import Lexicon
from purepos.common.statistics import Statistics
from purepos.model.probmodel import BaseProbabilityModel
from purepos.common import lemma
from purepos.model.combiner import BaseCombiner
from purepos.model.suffixtree import BaseSuffixTree, HashLemmaTree, HashSuffixTree
from purepos.model.suffixguesser import BaseSuffixGuesser
from purepos.model.ngram import NGramModel
from purepos.model.lemmaunigrammodel import LemmaUnigramModel


class CompiledModelData:
    def __init__(self):
        self.unigram_lemma_model = LemmaUnigramModel()
        self.lemma_guesser = BaseSuffixGuesser()
        self.suffix_lemma_model = BaseSuffixGuesser()
        self.combiner = BaseCombiner()
        self.tag_transition_model = BaseProbabilityModel()
        self.standard_emission_model = BaseProbabilityModel()
        self.spec_tokens_emission_model = BaseProbabilityModel()
        self.lower_case_suffix_guesser = BaseSuffixGuesser()
        self.upper_case_suffix_guesser = BaseSuffixGuesser()
        self.apriori_tag_probs = dict()


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
        self.combiner = lemma.default_combiner()

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


class ModelData:
    # todo paraméterezhető legyen MAJD!
    EOS_TAG = "</S>"
    BOS_TAG = "<S>"
    BOS_TOKEN = "<SB>"
    EOS_TOKEN = "<SE>"

    def __init__(self, tagging_order: int,
                 emission_order: int,
                 suffix_length: int,
                 rare_frequency: int,
                 standard_tokens_lexicon: Lexicon,
                 spec_tokens_lexicon: Lexicon,
                 tag_vocabulary: BaseVocabulary):
        self.tagging_order = tagging_order
        self.emission_order = emission_order
        self.suffix_length = suffix_length
        self.rare_frequency = rare_frequency
        self.standard_tokens_lexicon = standard_tokens_lexicon
        self.spec_tokens_lexicon = spec_tokens_lexicon
        self.tag_vocabulary = tag_vocabulary
        self.eos_index = tag_vocabulary.add_element(ModelData.EOS_TAG)
        self.bos_index = tag_vocabulary.add_element(ModelData.BOS_TAG)

    @staticmethod
    def create(tagging_order: int,
               emission_order: int,
               suffix_length: int,
               rare_frequency: int):
        return ModelData(tagging_order, emission_order, suffix_length, rare_frequency,
                         Lexicon(), Lexicon, IntVocabulary())
