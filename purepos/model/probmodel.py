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
from purepos.model.trienode import IntTrieNode, FloatTrieNode


class BaseProbabilityModel:
    def __init__(self):
        self.element_mapper = None
        self.context_mapper = None

    def prob(self, context: list, word) -> float:
        pass

    def log_prob(self, context: list, word) -> float:
        pass


class OneWordLexicalModel(BaseProbabilityModel):
    # todo: Ez eredetileg common: package hu.ppke.itk.nlpg.purepos.common;
    def __init__(self, probs: dict, word: str):
        super().__init__()
        self.probs = probs
        self.word = word

    def prob(self, context: list, word: str) -> float:
        return math.exp(self.log_prob(context, word))

    def log_prob(self, context: list, word: str) -> float:
        if self.element_mapper is not None:
            word = self.element_mapper.map(word)
        if self.context_mapper is not None:
            context = self.context_mapper.map_list(context)
        tag = context[-1]
        if word == self.word and tag in self.probs.keys():
            return self.probs[tag]
        return float("-inf")


class ProbModel(BaseProbabilityModel):
    def __init__(self, orig_root: IntTrieNode, lambdas: list):
        self.root = self.create_root(orig_root, lambdas)
        super().__init__()

    def prob(self, context: list, word) -> float:
        if self.element_mapper is not None:
            word = self.element_mapper.map(word)
        if self.context_mapper is not None:
            context = self.context_mapper.map_list(context)

        node = self.root
        find_more = True
        for prev in context[::-1]:
            find_more = node.has_child(prev) and node.child_nodes[prev].has_word(word)
            if not find_more:
                break
            node = node.get_child(prev)
            # prev = con
        if node.has_word(word):
            return node.words[word]
        else:
            return 0.0

    def log_prob(self, context: list, word) -> float:
        prob = self.prob(context, word)
        return math.log(prob) if prob > 0 else -99.0

    def word_probs(self, context):
        raise NotImplementedError("Is it used?")
        # todo törölni, ha nem kell.

    def create_root(self, node: IntTrieNode, lambdas: list) -> FloatTrieNode:
        new_root = self.calc_probs(node)
        for k, v in new_root.words.items():
            prob = lambdas[0] + lambdas[1] * v
            new_root.add_word_prob(k, prob)
        words = new_root.words
        for child in node.child_nodes.values():
            ch = self.create_child(child, words, lambdas, 2)
            # new_root.add_child(ch)
            new_root.child_nodes[ch.id_] = ch
        return new_root

    def create_child(self,
                     original_node: IntTrieNode, parent_words: dict, lambdas: list, level: int)\
            -> FloatTrieNode:
        if len(lambdas) > level:
            node = self.calc_probs(original_node)
            lamb = lambdas[level]
            for k, v in original_node.words.items():
                prob = parent_words[k]
                prob += lamb * original_node.apriori_prob(k)
                node.add_word_prob(k, prob)

            for child in original_node.child_nodes.values():
                ch = self.create_child(child, node.words, lambdas, level+1)
                if ch is not None:
                    # node.add_child(ch)
                    node.child_nodes[ch.id_] = ch
            return node
        else:
            return None

    @staticmethod
    def calc_probs(node: IntTrieNode) -> FloatTrieNode:
        new_root = FloatTrieNode(node.id_)
        for word in node.words.keys():
            tmp_prb = node.apriori_prob(word)
            new_root.add_word_prob(word, tmp_prb)
        return new_root
