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
from collections import Counter
from purepos.common.lemmatransformation import LemmaTransformation
from purepos.common.spectokenmatcher import SpecTokenMatcher
from purepos.common.corpusrepresentation import CorpusReader, Token
from purepos.common.util import Statistics
from purepos.configuration import Configuration
from purepos.model.hashsuffixtree import HashSuffixTree
from purepos.model.mapper import TagMapper
from purepos.model.ngrammodel import NGramModel
from purepos.model.vocabulary import Lexicon, IntVocabulary, LemmaUnigramModel


class Model:
    """Raw model from parsed analysed corpora or loaded saved model.
    """
    def last_stat(self) -> Statistics:
        return self.stat

    def __init__(self, tagging_order: int, emission_order: int, suffix_length: int, rare_frequency: int,
                 spec_token_matcher: SpecTokenMatcher, conf: Configuration, suffix_tree_from_rare_lemmas: bool):
        self.spec_token_matcher = spec_token_matcher
        self.tagging_order = tagging_order
        self.emission_order = emission_order
        self.suffix_length = suffix_length
        self.rare_frequency = rare_frequency
        self.conf = conf
        self.suffix_tree_from_rare_lemmas = suffix_tree_from_rare_lemmas

        self.stat = Statistics()  # Statistics about trainig
        self.corpus_types_w_count = Counter()

        # Ngram model for labels: computes the probability of a tag in a particular context and the apriori tag probs
        self.tag_transition_model = NGramModel(self.tagging_order + 1)  # P(t_i|..., t_i-2, t_i-1) and P(t_i)

        # Ngram model for the original wordforms and labels preceeding them
        self.standard_emission_model = NGramModel(self.emission_order + 1)  # P(t_i|w_i)

        # Ngram model for special tokens (punctuations, numbers etc.) and labels preceeding them
        self.spec_tokens_emission_model = NGramModel(2)  # P(t_i|wspec_i)

        self.standard_tokens_lexicon = Lexicon()
        self.standard_tokens_stem_lexicon = Lexicon()
        self.spec_tokens_lexicon = Lexicon()

        self.tag_vocabulary = IntVocabulary()
        self.bos_index = self.tag_vocabulary.add_element(self.conf.BOS_TAG)
        self.eos_index = self.tag_vocabulary.add_element(self.conf.EOS_TAG)

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
        from purepos.model.combiner import LogLinearBiCombiner
        self.combiner = LogLinearBiCombiner(self.conf)

    def train(self, document: list):
        # todo read lines by lines. See the issue:
        # https://github.com/ppke-nlpg/purepos-python3/issues/5
        for sentence in (sent for para in document for sent in para):
            # add sentence markers
            sentence = list(sentence)  # XXX REMÉLEM ÍGY JÓ! Le kell másolni különben megváltoztatja a doc-ot...
            sentence.insert(0, Token(self.conf.BOS_TOKEN, None, self.conf.BOS_TAG))
            self.stat.increment_sentence_count()  # Add sentence
            # Visszafelé kell haladni a tag szótár felépítésekor
            # todo: változtat az eredményen, ha előre haladunk és nem fodítjuk meg a tags-et?
            # (Az indexek felcserélésén kívül?)
            tags = [self.tag_vocabulary.add_element(token.tag) for token in sentence[::-1]]
            tags.reverse()

            self.tag_transition_model.add_word(tags, self.eos_index)
            for pos in range(len(sentence)-1, -1, -1):
                token = sentence[pos]
                if token.token != self.conf.BOS_TOKEN:
                    token.simplify_lemma()
                word = token.token
                lemma = token.stem
                tag = tags[pos]
                context = tags[0:pos+1]
                prev_tags = context[:-1]

                if word != self.conf.BOS_TOKEN and word != self.conf.EOS_TOKEN:
                    self.stat.increment_token_count()
                    self.lemma_unigram_model[lemma] += 1  # Store lemma
                    lemmatrans = LemmaTransformation(word, lemma, tag, self.conf.transformation)
                    self.lemma_suffix_tree.add_word(word, lemmatrans, 1, lemmatrans.min_cut_length())

                    self.corpus_types_w_count[token] += 1  # Frequency of every unique token (type) in the corpus
                    self.tag_transition_model.add_word(prev_tags, tag)
                    self.standard_tokens_lexicon.add_token(word, tag)
                    self.standard_tokens_stem_lexicon.add_token(lemma, (word, tag))  # Used for Guesser building
                    self.standard_emission_model.add_word(context, word)
                    spec_name = self.spec_token_matcher.match_lexical_element(word)
                    if spec_name is not None:
                        self.spec_tokens_emission_model.add_word(context, spec_name)
                        self.spec_tokens_lexicon.add_token(spec_name, tag)
        # Training: build suffix trees after the input is read
        if self.suffix_tree_from_rare_lemmas:
            for stem in self.standard_tokens_stem_lexicon.keys():
                # Checking for lemma rareness instead of word rareness...
                if self.standard_tokens_stem_lexicon.word_count(stem) <= self.rare_frequency:  # Is rare?
                    for word_tag in self.standard_tokens_stem_lexicon.get_all(stem).keys():
                        word = word_tag[0]  # Just the word, tag not needed...
                        self.add_rare_to_suffixtree(word)
        else:
            for word, tag_count in self.standard_tokens_lexicon.items():
                if self.standard_tokens_lexicon.word_count(word) <= self.rare_frequency:  # Is rare?
                    self.add_rare_to_suffixtree(word)

        # Compile model (almost)...
        self.tag_transition_model.count_word_apriori_probs()
        theta = HashSuffixTree.calculate_theta(self.tag_transition_model.word_apriori_probs)
        self.lower_suffix_tree.create_guesser(theta)
        self.upper_suffix_tree.create_guesser(theta)
        self.lemma_suffix_tree.create_guesser(theta)
        # self.suffix_lemma_model = self.lemma_freq_tree.create_guesser(theta)

        print(len(self.corpus_types_w_count))
        # Because combiner needs the document to compute lambdas! (Already aggregated the data...)
        self.combiner.calculate_params(self)

    def add_rare_to_suffixtree(self, word):  # To be able to define elswhere, that what is rare...
        lower_word = word.lower()
        if lower_word == word:  # Lower or upper case?
            suffix_tree_add_word = self.lower_suffix_tree.add_word
            stat_increment_guesser_items = self.stat.increment_lower_guesser_items
        else:
            suffix_tree_add_word = self.upper_suffix_tree.add_word
            stat_increment_guesser_items = self.stat.increment_upper_guesser_items
        for tag in self.standard_tokens_lexicon.get_all(word).keys():  # Add tag to the appropriate guesser
            word_tag_freq = self.standard_tokens_lexicon.wordcount_for_tag(word, tag)
            suffix_tree_add_word(lower_word, tag, word_tag_freq)
            stat_increment_guesser_items(word_tag_freq)

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
        self.combiner.conf = conf


class Trainer:
    """Trainer class. Its role is to build a Model from the analysed input."""
    def __init__(self, source: io.TextIOWrapper, field_separator, sentence_separator):
        """Instantiates a Trainer object.
        (In this version) it reads the whole input with the CorpusReader.
        :param source: TextIOWrapper input
        :param field_separator: Separator for fields
        :param sentence_separator: Separator for sentences
        """
        self.stat = Statistics()
        reader = CorpusReader(field_sep=field_separator, sentence_sep=sentence_separator)
        self.document = reader.read_from_io(source)  # todo egybe beolvassa a memóriába.

    def train(self, tag_order: int,
              emission_order: int,
              max_suffix_length: int,
              rare_frequency: int, spec_token_matcher: SpecTokenMatcher,
              conf: Configuration,
              suff_tree_from_rare_lemmas: bool) -> Model:
        return self.train_model(Model(tag_order, emission_order, max_suffix_length, rare_frequency, spec_token_matcher,
                                      conf, suff_tree_from_rare_lemmas))

    def train_model(self, model: Model) -> Model:
        model.train(self.document)
        self.stat = model.last_stat()
        return model
