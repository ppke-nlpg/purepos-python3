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

import math
from purepos.model.vocabulary import IntVocabulary, TrieNode


class NGramModel:
    def __init__(self, n: int):
        self.n = n
        self.root = TrieNode(IntVocabulary.extremal_element())
        self.lambdas = []
        self.word_apriori_probs = None
        self.apriori_word_mapper = None
        self.context_mapper = None
        self.element_mapper = None

    def add_word(self, context: list, word):
        act = self.root
        act.add_word(word)
        for c in context[:-self.n:-1]:
            act = act.add_child(c)
            act.add_word(word)

    def create_probability_model(self, context_mapper, element_mapper):
        # Add mappings...
        self.context_mapper = context_mapper
        self.element_mapper = element_mapper
        # Calculate lambdas...
        self.lambdas = [0.0 for _ in range(0, self.n + 1, 1)]
        self._iterate(self.root, [])
        s = sum(self.lambdas)
        if s > 0:
            self.lambdas = [l / s for l in self.lambdas]
        self._create_root(self.root, self.lambdas)

    def log_prob(self, context: list, word, unk_value) -> float:
        # todo: Somehow indicate if the mapper maps to something that were never seen (new in vocabulary)
        # Beacause then we can skip climbing the suffix trie and return unk_value...
        if self.element_mapper is not None:
            word = self.element_mapper.map(word)
        if self.context_mapper is not None:
            context = self.context_mapper.map_list(context)
        node = self.root
        for prev in context[::-1]:  # Find more
            if prev in node.child_nodes.keys() and word in node.child_nodes[prev].words.keys():
                node = node.child_nodes[prev]
            else:
                break
        prob = node.words.get(word, 0.0)
        return math.log(prob) if prob > 0 else unk_value

    def apriori_log_prob(self, tag, unk_value):
        if self.apriori_word_mapper is not None:
            tag = self.apriori_word_mapper.map(tag)
        elem = self.word_apriori_probs.get(tag)
        if elem is not None:
            return math.log(elem)
        return unk_value

    def count_word_apriori_probs(self):
        self.word_apriori_probs = {k: v / self.root.num for k, v in self.root.words.items()}

    @staticmethod
    def _calculate_modified_freq_val(node_list: list, position: int, word) -> float:
        context_freq = node_list[position].num
        word_freq = node_list[position].words[word]
        if context_freq == 1 or word_freq == 1:
            return -1
        else:
            return (word_freq - 1) / (context_freq - 1)

    def _iterate(self, node: TrieNode, acc: list):
        acc.append(node)
        if node.child_nodes is None or len(node.child_nodes) == 0:
            for word in node.words.keys():
                max_pos, max_val = max(((pos, self._calculate_modified_freq_val(acc, pos, word))  # max_pos, max_val
                                        for pos in range(len(acc))), key=lambda p: p[1], default=(None, None))
                index = max_pos + 1
                if max_val != -1:
                    self.lambdas[index] = self.lambdas[index] + node.words[word]
        else:
            for child in node.child_nodes.values():
                self._iterate(child, acc)
        acc.pop()

    def _create_root(self, node: TrieNode, lambdas: list) -> TrieNode:
        new_root = self._calc_probs(node)
        new_root.words = {k: lambdas[0] + lambdas[1] * v for k, v in new_root.words.items()}
        for child in node.child_nodes.values():
            ch = self._create_child(child, new_root.words, lambdas, 2)
            new_root.child_nodes[ch.id_] = ch
        return new_root

    # Recursive function!
    def _create_child(self, original_node: TrieNode, parent_words: dict, lambdas: list, level: int) -> TrieNode:
        if len(lambdas) > level:
            node = self._calc_probs(original_node)
            node.words = {k: parent_words[k] + lambdas[level] * original_node.apriori_prob(k)
                          for k, v in original_node.words.items()}
            for child in original_node.child_nodes.values():
                ch = self._create_child(child, node.words, lambdas, level + 1)
                if ch is not None:
                    node.child_nodes[ch.id_] = ch
            return node
        else:
            return None

    @staticmethod
    def _calc_probs(node: TrieNode) -> TrieNode:
        new_root = TrieNode(node.id_, node_type=float)
        new_root.words = {word: node.apriori_prob(word) for word in node.words.keys()}
        return new_root
