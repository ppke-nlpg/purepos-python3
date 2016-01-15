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

from corpusreader.containers import Document, Sentence, Token
from purepos.cli.configuration import Configuration
from purepos.common import util
from purepos.common.lemmatransformation import def_lemma_representation
from purepos.common.spectokenmatcher import SpecTokenMatcher
from purepos.common.statistics import Statistics
from purepos.model.suffixguesser import HashSuffixTree
from purepos.model.ngrammodel import NGramModel
from purepos.model.vocabulary import LemmaUnigramModel, Lexicon, IntVocabulary
from purepos.model.mapper import TagMapper


class CompiledModelData:
    def __init__(self):
        self.unigram_lemma_model = LemmaUnigramModel()
        self.lemma_guesser = None
        self.suffix_lemma_model = None
        from purepos.model.combiner import BaseCombiner
        # Két lemmagyakorisági modell kombinációját számoló objektum
        self.combiner = BaseCombiner()
        # Az adott tag valsége az előzőek fv-jében
        self.tag_transition_model = None
        # Szóalakok gyakorisága a tag függvényében
        self.standard_emission_model = None
        # Írásjelek, számok, stb. gyakorisága a tag függvényében
        self.spec_tokens_emission_model = None
        # Suffix guesserek a kezdőbetű szerint felépítve.
        self.lower_case_suffix_guesser = None
        self.upper_case_suffix_guesser = None
        # tag ngram modellből számolt apriori tag valószínűségek
        self.apriori_tag_probs = dict()

    # ez a utilból került ide.
    def add_mappings(self,
                     tag_vocabulary: IntVocabulary,
                     tag_mappings: list):
        mapper = TagMapper(tag_vocabulary, tag_mappings)
        self.standard_emission_model.context_mapper = mapper
        self.spec_tokens_emission_model.context_mapper = mapper

        self.tag_transition_model.context_mapper = mapper
        self.tag_transition_model.element_mapper = mapper

        self.lower_case_suffix_guesser.mapper = mapper
        self.upper_case_suffix_guesser.mapper = mapper


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
                 tag_vocabulary: IntVocabulary):
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
                         Lexicon(), Lexicon(), IntVocabulary())


class CompiledModel:
    def __init__(self, comp_model_data: CompiledModelData, model_data: ModelData):
        self.data = model_data
        self.compiled_data = comp_model_data


class RawModelData:
    def __init__(self, tagging_order, emission_order):
        self.stat = Statistics()  # Statistics about trainig
        # Címkék ngram modellje
        self.tag_ngram_model = NGramModel(tagging_order + 1)
        # Eredeti szóalakok és a megelőző cimkék modellje
        self.std_emission_ngram_model = NGramModel(emission_order + 1)
        # Speciális tokenek és a megelőző cimkék modellje
        self.spec_emission_ngram_model = NGramModel(2)
        self.eos_tag = None
        # Lemma suffix gyakorisági táblázat (HashLemmaTree volt.)
        self.lemma_suffix_tree = HashSuffixTree(100)
        # Lemma gyakorisági táblázat
        self.lemma_freq_tree = HashSuffixTree(5)
        # Lemma gyakorisági táblázat
        self.lemma_unigram_model = LemmaUnigramModel()
        # Szóalakok suffix gyakorisági táblázata kis- és nagybetűérzékenyen.
        self.lower_suffix_tree = None  # HashSuffixTree(0)
        self.upper_suffix_tree = None  # HashSuffixTree(0)
        self.lemma_lambdas = list()
        # LogLinearBiCombiner a guesserből és az unigram modellből származó adatok kombinálásához.
        from purepos.model.combiner import default_combiner
        self.combiner = default_combiner()

    def compile(self) -> CompiledModelData:
        c = CompiledModelData()
        c.unigram_lemma_model = self.lemma_unigram_model
        c.tag_transition_model = self.tag_ngram_model.create_probability_model()
        c.standard_emission_model = self.std_emission_ngram_model.create_probability_model()
        c.spec_tokens_emission_model = self.spec_emission_ngram_model.create_probability_model()
        c.apriori_tag_probs = self.tag_ngram_model.word_apriori_probs()
        theta = HashSuffixTree.calculate_theta(c.apriori_tag_probs)
        c.lower_case_suffix_guesser = self.lower_suffix_tree.create_guesser(theta)
        c.upper_case_suffix_guesser = self.upper_suffix_tree.create_guesser(theta)
        c.lemma_guesser = self.lemma_suffix_tree.create_guesser(theta)
        c.suffix_lemma_model = self.lemma_freq_tree.create_guesser(theta)
        c.combiner = self.combiner
        return c


class RawModel:
    """Raw model from parsed analysed corpora or loaded saved model.
    """
    @staticmethod
    def store_lemma(word: str,
                    lemma: str,
                    tag: int,
                    _: str,  # tagstring
                    raw_modeldata: RawModelData):
        raw_modeldata.lemma_unigram_model[lemma] += 1
        cnt = 1
        lemmatrans = def_lemma_representation(word, lemma, tag)
        raw_modeldata.lemma_suffix_tree.add_word(word, lemmatrans, cnt, lemmatrans.min_cut_length())

    @staticmethod
    def add_sentence_markers(sentence: Sentence):
        sentence.insert(0, Token(ModelData.BOS_TOKEN, None, ModelData.BOS_TAG))

    def __init__(self, model_data: ModelData):
        # __init__(self, tagging_order: int, emission_order: int, suffix_length: int, rare_freq:
        # int):
        # ModelData.create(tagging_order, emission_order, suffix_length, rare_freq)
        self.data = model_data
        self.raw_model_data = RawModelData(model_data.tagging_order, model_data.emission_order)

    def train(self, document: Document):
        # todo read lines by lines. See the issue:
        # https://github.com/ppke-nlpg/purepos-python3/issues/5
        self.raw_model_data.eos_tag = self.data.tag_vocabulary.add_element(ModelData.EOS_TAG)
        for sentence in document.sentences():
            mysentence = Sentence(sentence)
            self.add_sentence_markers(mysentence)
            self.add_sentence(mysentence)
        self.build_suffix_trees()
        self.raw_model_data.combiner.calculate_params(document, self.raw_model_data, self.data)

    def add_sentence(self, sentence: Sentence):
        self.raw_model_data.stat.increment_sentence_count()
        tags = []
        # Visszafelé kell haladni a tag szótár felépítésekor
        # todo: változtat az eredményen, ha előre haladunk és nem fodítjuk meg a tags-et?
        for token in sentence[::-1]:
            tags.append(self.data.tag_vocabulary.add_element(token.tag))
        tags.reverse()

        self.raw_model_data.tag_ngram_model.add_word(tags, self.raw_model_data.eos_tag)

        # for i, token in enumerate(sentence):
        for i in range(len(sentence)-1, -1, -1):
            token = sentence[i]
            if token.token != ModelData.BOS_TOKEN:
                token = util.simplify_lemma(token)
            word = token.token
            lem = token.stem
            tagstr = token.tag
            tag = tags[i]
            context = tags[0:i+1]
            prev_tags = context[:-1]

            if not (word == ModelData.BOS_TOKEN or word == ModelData.EOS_TOKEN):
                self.store_lemma(word, lem, tag, tagstr, self.raw_model_data)

                self.raw_model_data.tag_ngram_model.add_word(prev_tags, tag)
                self.raw_model_data.stat.increment_token_count()
                self.data.standard_tokens_lexicon.add_token(word, tag)
                self.raw_model_data.std_emission_ngram_model.add_word(context, word)
                spec_name = SpecTokenMatcher.match_lexical_element(word)
                if spec_name is not None:
                    self.raw_model_data.spec_emission_ngram_model.add_word(context, spec_name)
                    self.data.spec_tokens_lexicon.add_token(spec_name, tag)

    def build_suffix_trees(self):
        # Tanuláskor, beolvasás után suffixtree-k építése.
        self.raw_model_data.lower_suffix_tree = HashSuffixTree(self.data.suffix_length)
        self.raw_model_data.upper_suffix_tree = HashSuffixTree(self.data.suffix_length)
        for word, m in self.data.standard_tokens_lexicon.representation.items():
            word_freq = self.data.standard_tokens_lexicon.word_count(word)
            if word_freq <= self.data.rare_frequency:
                lower_word = word.lower()
                islower = lower_word == word
                for tag in m.keys():
                    word_tag_freq = self.data.standard_tokens_lexicon.wordcount_for_tag(word, tag)
                    if islower:
                        self.raw_model_data.lower_suffix_tree.add_word(lower_word, tag, word_tag_freq)
                        self.raw_model_data.stat.increment_lower_guesser_items(word_tag_freq)
                    else:
                        self.raw_model_data.upper_suffix_tree.add_word(lower_word, tag, word_tag_freq)
                        self.raw_model_data.stat.increment_upper_guesser_items(word_tag_freq)

    def compile(self, conf: Configuration) -> CompiledModel:
        # Create a CompiledModel from this RawModel
        self.data.tag_vocabulary.store_max_element()
        comp_model_data = self.raw_model_data.compile()
        comp_model_data.add_mappings(self.data.tag_vocabulary, conf.tag_mappings)
        return CompiledModel(comp_model_data, self.data)

    def last_stat(self) -> Statistics:
        return self.raw_model_data.stat
