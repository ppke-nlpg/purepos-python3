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

from corpusreader.containers import Token
from purepos.cli.configuration import Configuration
from purepos.common.lemmatransformation import def_lemma_representation
from purepos.common.spectokenmatcher import SpecTokenMatcher
from purepos.common.statistics import Statistics
from purepos.model.hashsuffixtree import HashSuffixTree
from purepos.model.ngrammodel import NGramModel
from purepos.model.vocabulary import LemmaUnigramModel, Lexicon, IntVocabulary
from purepos.model.mapper import TagMapper


class Model:
    """Raw model from parsed analysed corpora or loaded saved model.
    """
    # todo paraméterezhető legyen MAJD!
    EOS_TAG = "</S>"
    BOS_TAG = "<S>"
    BOS_TOKEN = "<SB>"
    EOS_TOKEN = "<SE>"

    def last_stat(self) -> Statistics:
        return self.stat

    def __init__(self, tagging_order: int, emission_order: int, suffix_length: int, rare_frequency: int):
        self.tagging_order = tagging_order
        self.emission_order = emission_order
        self.suffix_length = suffix_length
        self.rare_frequency = rare_frequency

        self.stat = Statistics()  # Statistics about trainig

        # Ngram model for labels: computes the probability of a tag in a particular context and the apriori tag probs
        self.tag_transition_model = NGramModel(self.tagging_order + 1)  # P(t_i|..., t_i-2, t_i-1) and P(t_i)

        # Ngram model for the original wordforms and labels preceeding them
        self.standard_emission_model = NGramModel(self.emission_order + 1)  # P(t_i|w_i)

        # Ngram model for special tokens (punctuations, numbers etc.) and labels preceeding them
        self.spec_tokens_emission_model = NGramModel(2)  # P(t_i|wspec_i)

        self.standard_tokens_lexicon = Lexicon()
        self.spec_tokens_lexicon = Lexicon()

        self.tag_vocabulary = IntVocabulary()
        self.bos_index = self.tag_vocabulary.add_element(Model.BOS_TAG)
        self.eos_index = self.tag_vocabulary.add_element(Model.EOS_TAG)

        # Lemma suffix frequency table (ex HashLemmaTree class) 100 is enough for max lemma length...
        self.lemma_suffix_tree = HashSuffixTree(100)
        self.lemma_guesser = None
        # Lemma suffix frequency table Max suff len miért 5? LogLinearTriCombiner használja egyedül
        # self.lemma_freq_tree = HashSuffixTree(5)
        # self.suffix_lemma_model = None

        self.lemma_unigram_model = LemmaUnigramModel()  # Lemma suffix frequency table (i.e. Counter with  probs)
        # Word suffix frequency table, case sensititve. This trees are built during the training phase...
        self.lower_suffix_tree = HashSuffixTree(self.suffix_length)  # They will become suffixguessers...
        self.upper_suffix_tree = HashSuffixTree(self.suffix_length)

        # LogLinearBiCombiner: combine data form the guesser and the unigram model
        from purepos.model.combiner import default_combiner
        self.combiner = default_combiner()

    def train(self, document: list):
        # todo read lines by lines. See the issue:
        # https://github.com/ppke-nlpg/purepos-python3/issues/5
        for sentence in (sent for para in document for sent in para):
            # add sentence markers
            sentence = list(sentence)  # XXX REMÉLEM ÍGY JÓ! Le kell másolni különben megváltoztatja a doc-ot...
            sentence.insert(0, Token(Model.BOS_TOKEN, None, Model.BOS_TAG))
            self.stat.increment_sentence_count()  # Add sentence
            # Visszafelé kell haladni a tag szótár felépítésekor
            # todo: változtat az eredményen, ha előre haladunk és nem fodítjuk meg a tags-et?
            # (Az indexek felcserélésén kívül?)
            tags = [self.tag_vocabulary.add_element(token.tag) for token in sentence[::-1]]
            tags.reverse()

            self.tag_transition_model.add_word(tags, self.eos_index)
            for i in range(len(sentence)-1, -1, -1):
                token = sentence[i]
                if token.token != Model.BOS_TOKEN:
                    token.simplify_lemma()
                word = token.token
                lemma = token.stem
                tag = tags[i]
                context = tags[0:i+1]
                prev_tags = context[:-1]

                if word != Model.BOS_TOKEN and word != Model.EOS_TOKEN:
                    self.stat.increment_token_count()
                    self.lemma_unigram_model[lemma] += 1  # Store lemma
                    lemmatrans = def_lemma_representation(word, lemma, tag)
                    self.lemma_suffix_tree.add_word(word, lemmatrans, 1, lemmatrans.min_cut_length())

                    self.tag_transition_model.add_word(prev_tags, tag)
                    self.standard_tokens_lexicon.add_token(word, tag)
                    self.standard_emission_model.add_word(context, word)
                    spec_name = SpecTokenMatcher.match_lexical_element(word)
                    if spec_name is not None:
                        self.spec_tokens_emission_model.add_word(context, spec_name)
                        self.spec_tokens_lexicon.add_token(spec_name, tag)

        for word, m in self.standard_tokens_lexicon.items():  # Training: build suffix trees after the input is read
            if self.standard_tokens_lexicon.word_count(word) <= self.rare_frequency:  # Is rare?
                lower_word = word.lower()
                if lower_word == word:  # Lower or upper case?
                    suffix_tree_add_word = self.lower_suffix_tree.add_word
                    stat_increment_guesser_items = self.stat.increment_lower_guesser_items
                else:
                    suffix_tree_add_word = self.upper_suffix_tree.add_word
                    stat_increment_guesser_items = self.stat.increment_upper_guesser_items
                for tag in m.keys():  # Add to the appropriate guesser
                    word_tag_freq = self.standard_tokens_lexicon.wordcount_for_tag(word, tag)
                    suffix_tree_add_word(lower_word, tag, word_tag_freq)
                    stat_increment_guesser_items(word_tag_freq)

        # Compile model (almost)...
        self.tag_transition_model.count_word_apriori_probs()
        theta = HashSuffixTree.calculate_theta(self.tag_transition_model.word_apriori_probs)
        self.lower_suffix_tree.create_guesser(theta)
        self.upper_suffix_tree.create_guesser(theta)
        self.lemma_suffix_tree.create_guesser(theta)
        # self.suffix_lemma_model = self.lemma_freq_tree.create_guesser(theta)

        # Because combiner needs the document to compute lambdas!
        self.combiner.calculate_params(document, self)

    def compile(self, conf: Configuration):  # Create a CompiledModel from this Model
        self.tag_vocabulary.store_max_element()

        # Compute lambdas and add mappings...
        mapper = TagMapper(self.tag_vocabulary, conf.tag_mappings)
        self.tag_transition_model.create_probability_model(mapper, mapper)
        self.standard_emission_model.create_probability_model(mapper, None)     # XXX miért is nincs ilyen?
        self.spec_tokens_emission_model.create_probability_model(mapper, None)  # XXX miért is nincs ilyen?

        self.lower_suffix_tree.mapper = mapper
        self.upper_suffix_tree.mapper = mapper

        self.tag_transition_model.apriori_word_mapper = mapper
