#!/usr/bin/env Python3
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

from docmodel.containers import Document, Sentence
from docmodel.token import Token
from purepos.model.modeldata import ModelData, RawModelData, CompiledModelData
from purepos.model.suffixtree import HashSuffixTree
from purepos.common.spectokenmatcher import SpecTokenMatcher
from purepos.common.statistics import Statistics
from purepos.common import util, lemma
from purepos.cli.configuration import Configuration


class BaseModel:
    """
    An object of this class is representing the model of a POS tagger.
    Getterek helyett: model.data.<attribútum>
    """
    def __init__(self, data: ModelData):
        self.data = data


class CompiledModel(BaseModel):
    def __init__(self, comp_model_data: CompiledModelData, model_data: ModelData):
        super().__init__(model_data)
        self.compiled_data = comp_model_data


class RawModel(BaseModel):
    @staticmethod
    def add_sentence_markers(sentence: Sentence):
        sentence.insert(0, Token(ModelData.BOS_TOKEN, None, ModelData.BOS_TAG))

    def __init__(self, model_data: ModelData):
        # __init__(self, tagging_order: int, emission_order: int, suffix_length: int, rare_freq:
        # int):
        # ModelData.create(tagging_order, emission_order, suffix_length, rare_freq)
        super().__init__(model_data)
        self.raw_model_data = RawModelData(model_data.tagging_order, model_data.emission_order)

    def train(self, document: Document):
        self.raw_model_data.eos_tag = self.data.tag_vocabulary.add_element(ModelData.EOS_TAG)
        for sentence in document.sentences():
            mysentence = Sentence(sentence)
            self.add_sentence_markers(mysentence)
            self.add_sentence(mysentence)
        self.build_suffix_trees()
        self.raw_model_data.combiner.calculate_params(document, self.raw_model_data, self.data)

    def add_sentence(self, sentence: Sentence):
        self.raw_model_data.stat.increment_sentence_count()
        spec_matcher = SpecTokenMatcher()
        tags = []
        for token in sentence:
            tags.append(self.data.tag_vocabulary.add_element(token.tag))

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
            context = tags[0:i+1]  # todo. sorrend? bedrótozva i+1?
            prev_tags = context[:-1]

            if word != ModelData.BOS_TOKEN or word == ModelData.EOS_TOKEN:
                lemma.store_lemma(word, lem, tag, tagstr, self.raw_model_data)

                self.raw_model_data.tag_ngram_model.add_word(prev_tags, tag)
                self.raw_model_data.stat.increment_token_count()
                self.data.standard_tokens_lexicon.add_token(word, tag)
                self.raw_model_data.std_emission_ngram_model.add_word(context, word)
                spec_name = spec_matcher.match_lexical_element(word)
                if spec_name is not None:
                    self.raw_model_data.spec_emission_ngram_model.add_word(context, spec_name)
                    self.data.spec_tokens_lexicon.add_token(spec_name, tag)

    def build_suffix_trees(self):
        self.raw_model_data.lower_suffix_tree = HashSuffixTree(self.data.suffix_length)
        self.raw_model_data.upper_suffix_tree = HashSuffixTree(self.data.suffix_length)
        for word, m in self.data.standard_tokens_lexicon:
            word_freq = self.data.standard_tokens_lexicon.word_count(word)
            if word_freq <= self.data.rare_frequency:
                lower_word = word.lower()
                islower = lower_word == word
                for tag in m.keys():
                    word_tag_freq = self.data.standard_tokens_lexicon.wordcount_for_tag(word, tag)
                    if islower:
                        self.raw_model_data.lower_suffix_tree.add_word(
                            lower_word, tag, word_tag_freq)
                        self.raw_model_data.stat.increment_lower_guesser_items(word_tag_freq)
                    else:
                        self.raw_model_data.upper_suffix_tree.add_word(
                            lower_word, tag, word_tag_freq)
                        self.raw_model_data.stat.increment_upper_guesser_items(word_tag_freq)

    def compile(self, conf: Configuration) -> CompiledModel:
        self.data.tag_vocabulary.store_max_element()
        comp_model_data = self.raw_model_data.compile()
        util.add_mappings(comp_model_data, self.data.tag_vocabulary, conf.tag_mappings())
        return CompiledModel(comp_model_data, self.data)

    def last_stat(self) -> Statistics:
        return self.raw_model_data.stat
