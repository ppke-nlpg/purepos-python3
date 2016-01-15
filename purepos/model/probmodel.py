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
from purepos.model.vocabulary import TrieNode

UNKNOWN_VALUE = -99.0


# Hosszú távon kifaktorálható?
class BaseProbabilityModel:
    def __init__(self):
        self.element_mapper = None
        self.context_mapper = None

    def prob(self, context: list, word) -> float:
        pass

    def log_prob(self, context: list, word) -> float:
        pass


class OneWordLexicalModel(BaseProbabilityModel):
    # Csak az analysisqueue-ban. Valóban kell?
    # Ez eredetileg common: package hu.ppke.itk.nlpg.purepos.common;
    def __init__(self, probs: dict, word: str):
        super().__init__()
        self.probs = probs
        self.word = word

    def log_prob(self, context: list, word: str) -> float:
        if self.element_mapper is not None:
            word = self.element_mapper.map(word)
        if self.context_mapper is not None:
            context = self.context_mapper.map_list(context)
        tag = context[-1]
        if word == self.word and tag in self.probs.keys():
            return self.probs[tag]
        return UNKNOWN_VALUE


class ProbModel(BaseProbabilityModel):
    def __init__(self, orig_root: TrieNode, lambdas: list):
        self.root = self.create_root(orig_root, lambdas)
        super().__init__()

    def log_prob(self, context: list, word) -> float:
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
        return math.log(prob) if prob > 0 else UNKNOWN_VALUE

    def create_root(self, node: TrieNode, lambdas: list) -> TrieNode:
        new_root = self.calc_probs(node)
        new_root.words = {k: lambdas[0] + lambdas[1] * v for k, v in new_root.words.items()}
        for child in node.child_nodes.values():
            ch = self.create_child(child, new_root.words, lambdas, 2)
            new_root.child_nodes[ch.id_] = ch
        return new_root

    def create_child(self, original_node: TrieNode, parent_words: dict, lambdas: list, level: int) -> TrieNode:
        if len(lambdas) > level:
            node = self.calc_probs(original_node)
            node.words = {k: parent_words[k] + lambdas[level] * original_node.apriori_prob(k)
                          for k, v in original_node.words.items()}
            for child in original_node.child_nodes.values():
                ch = self.create_child(child, node.words, lambdas, level+1)
                if ch is not None:
                    node.child_nodes[ch.id_] = ch
            return node
        else:
            return None

    @staticmethod
    def calc_probs(node: TrieNode) -> TrieNode:
        new_root = TrieNode(node.id_, node_type=float)
        new_root.words = {word: node.apriori_prob(word) for word in node.words.keys()}
        return new_root
