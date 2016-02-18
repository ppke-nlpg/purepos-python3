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
from purepos.common import util
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
        # Ngram model for labels

        self.tag_ngram_model = NGramModel(self.tagging_order + 1)
        # Az adott tag valsége az előzőek fv-jében
        self.tag_transition_model = None
        # tag ngram modellből számolt apriori tag valószínűségek
        self.apriori_tag_probs = None

        # Ngram model for the original wordforms and labels preceeding them
        self.std_emission_ngram_model = NGramModel(self.emission_order + 1)
        # Szóalakok gyakorisága a tag függvényében
        self.standard_emission_model = None

        # Ngram model for special tokens and labels preceeding them
        self.spec_emission_ngram_model = NGramModel(2)
        # Írásjelek, számok, stb. gyakorisága a tag függvényében
        self.spec_tokens_emission_model = None

        self.standard_tokens_lexicon = Lexicon()
        self.spec_tokens_lexicon = Lexicon()

        self.tag_vocabulary = IntVocabulary()
        self.bos_index = self.tag_vocabulary.add_element(Model.BOS_TAG)
        self.eos_index = self.tag_vocabulary.add_element(Model.EOS_TAG)

        # Lemma suffix gyakorisági táblázat (HashLemmaTree volt.) Max suff len miért 100?
        self.lemma_suffix_tree = HashSuffixTree(100)
        self.lemma_guesser = None
        # Lemma gyakorisági táblázat Max suff len miért 5? LogLinearTriCombiner használja egyedül
        # self.lemma_freq_tree = HashSuffixTree(5)
        # self.suffix_lemma_model = None

        # Lemma gyakorisági táblázat (Counterből származtatott osztály, aminek van prob-ja)
        self.lemma_unigram_model = LemmaUnigramModel()
        # Szóalakok suffix gyakorisági táblázata kis- és nagybetűérzékenyen.
        # Tanuláskor, beolvasás után suffixtree-k építése.
        self.lower_suffix_tree = HashSuffixTree(self.suffix_length)
        self.upper_suffix_tree = HashSuffixTree(self.suffix_length)
        # Suffix guesserek a kezdőbetű szerint felépítve.
        self.lower_case_suffix_guesser = None
        self.upper_case_suffix_guesser = None

        # LogLinearBiCombiner a guesserből és az unigram modellből származó adatok kombinálásához.
        # Két lemmagyakorisági modell kombinációját számoló objektum
        from purepos.model.combiner import default_combiner
        self.combiner = default_combiner()

    def train(self, document: list):
        # todo read lines by lines. See the issue:
        # https://github.com/ppke-nlpg/purepos-python3/issues/5
        for sentence in (sent for para in document for sent in para):
            # add sentence markers
            sentence = list(sentence)  # XXX REMÉLEM ÍGY JÓ! Le kell másolni különben megváltoztatja a doc-ot...
            sentence.insert(0, Token(Model.BOS_TOKEN, None, Model.BOS_TAG))
            # Add sentence
            self.stat.increment_sentence_count()
            # Visszafelé kell haladni a tag szótár felépítésekor
            # todo: változtat az eredményen, ha előre haladunk és nem fodítjuk meg a tags-et?
            # (Az indexek felcserélésén kívül?)
            tags = [self.tag_vocabulary.add_element(token.tag) for token in sentence[::-1]]
            tags.reverse()

            self.tag_ngram_model.add_word(tags, self.eos_index)
            # for i, token in enumerate(sentence):
            for i in range(len(sentence)-1, -1, -1):
                token = sentence[i]
                if token.token != Model.BOS_TOKEN:
                    token = util.simplify_lemma(token)  # Innentől ModToken típus lenne, ha mappelné a lemmát...
                word = token.token
                lemma = token.stem
                tag = tags[i]
                context = tags[0:i+1]
                prev_tags = context[:-1]

                if word != Model.BOS_TOKEN and word != Model.EOS_TOKEN:
                    self.stat.increment_token_count()
                    # Store lemma
                    self.lemma_unigram_model[lemma] += 1
                    lemmatrans = def_lemma_representation(word, lemma, tag)
                    self.lemma_suffix_tree.add_word(word, lemmatrans, 1, lemmatrans.min_cut_length())

                    self.tag_ngram_model.add_word(prev_tags, tag)
                    self.standard_tokens_lexicon.add_token(word, tag)
                    self.std_emission_ngram_model.add_word(context, word)
                    spec_name = SpecTokenMatcher.match_lexical_element(word)
                    if spec_name is not None:
                        self.spec_emission_ngram_model.add_word(context, spec_name)
                        self.spec_tokens_lexicon.add_token(spec_name, tag)

        # Tanuláskor, beolvasás után suffixtree-k építése.
        for word, m in self.standard_tokens_lexicon.items():
            # Is rare?
            if self.standard_tokens_lexicon.word_count(word) <= self.rare_frequency:
                # Lower or upper case?
                lower_word = word.lower()
                if lower_word == word:
                    suffix_tree_add_word = self.lower_suffix_tree.add_word
                    stat_increment_guesser_items = self.stat.increment_lower_guesser_items
                else:
                    suffix_tree_add_word = self.upper_suffix_tree.add_word
                    stat_increment_guesser_items = self.stat.increment_upper_guesser_items
                # Add to the appropriate guesser
                for tag in m.keys():
                    word_tag_freq = self.standard_tokens_lexicon.wordcount_for_tag(word, tag)
                    suffix_tree_add_word(lower_word, tag, word_tag_freq)
                    stat_increment_guesser_items(word_tag_freq)

        # Compile model (almost)...
        self.apriori_tag_probs = self.tag_ngram_model.word_apriori_probs()
        theta = HashSuffixTree.calculate_theta(self.apriori_tag_probs)
        self.lower_suffix_tree.create_guesser(theta)
        self.upper_suffix_tree.create_guesser(theta)
        self.lemma_suffix_tree.create_guesser(theta)
        # self.suffix_lemma_model = self.lemma_freq_tree.create_guesser(theta)

        # Because combiner needs the document to compute lambdas!
        self.combiner.calculate_params(document, self)

    def compile(self, conf: Configuration):
        # Create a CompiledModel from this Model
        self.tag_vocabulary.store_max_element()

        # Compute lambdas...
        self.tag_transition_model = self.tag_ngram_model.create_probability_model()
        self.standard_emission_model = self.std_emission_ngram_model.create_probability_model()
        self.spec_tokens_emission_model = self.spec_emission_ngram_model.create_probability_model()

        # Add mappings
        mapper = TagMapper(self.tag_vocabulary, conf.tag_mappings)
        self.tag_transition_model.context_mapper = mapper
        self.standard_emission_model.context_mapper = mapper
        self.spec_tokens_emission_model.context_mapper = mapper

        self.tag_transition_model.element_mapper = mapper
        self.lower_suffix_tree.mapper = mapper
        self.upper_suffix_tree.mapper = mapper

        self.apriori_tag_probs.mapper = mapper
