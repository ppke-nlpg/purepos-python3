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

from purepos.model.trienode import IntTrieNode, BaseTrieNode
from purepos.model.vocabulary import IntVocabulary
from purepos.model.probmodel import ProbModel


class NGramModel:
    def __init__(self, n: int):
        self.n = n
        self.root = IntTrieNode(IntVocabulary.extremal_element())
        self.lambdas = []

    def add_word(self, context: list, word):
        act = self.root
        i = 0
        size = self.n - 1
        act.add_word(word)
        for c in context[::-1]:
            if not i < size:
                break
            act = act.add_child(c)
            act.add_word(word)
            i += 1

    def word_frequency(self, context: list, word) -> list:
        ret = list()
        ret.append(self.root.apriori_prob(word))
        act_node = self.root
        if context is not None and len(context) > 0:
            for c in context[::-1]:
                if act_node is None:
                    break
                prev = c
                if act_node.has_child(prev):
                    act_node = act_node.child_nodes[prev]
                    ret.append(act_node.apriori_prob(word))
                else:
                    for _ in context[context.index(c)::-1]:
                        ret.append(0.0)
                    act_node = None
        return ret

    @staticmethod
    def calculate_modified_freq_val(node_list: list, position: int, word) -> float:
        context_freq = node_list[position].num
        word_freq = node_list[position].words[word]
        if context_freq == 1 or word_freq == 1:
            return -1
        else:
            return (word_freq - 1) / (context_freq - 1)

    def find_max(self, l: list, word) -> tuple:
        if l is None or len(l) == 0:
            return None, None
        max_pos = -1
        max_val = 0.0
        for i, v in enumerate(l):
            val = self.calculate_modified_freq_val(l, i, word)
            if val > max_val:
                max_pos = i
                max_val = val
        return max_pos, max_val

    def calculat_ngram_lambdas(self):
        self.lambdas = [0.0 for _ in range(0, self.n+1, 1)]
        acc = []
        self.iterate(self.root, acc)

        s = 0.0
        self.lambdas[0] = 0.0
        for e in self.lambdas:
            s += e

    def iterate(self, node: BaseTrieNode, acc: list):
        acc.append(node)
        if node.child_nodes is None or len(node.child_nodes) == 0:
            for word in node.words.keys():
                mx = self.find_max(acc, word)
                index = mx[0] + 1
                if mx[1] != -1:
                    self.lambdas[index] = self.lambdas[index] + node.get_word(word)
        else:
            for child in node.child_nodes.values():
                self.iterate(child, acc)
        acc.pop()

    def create_probability_model(self) -> ProbModel:
        self.calculat_ngram_lambdas()
        return ProbModel(self.root, self.lambdas)

    def word_apriori_probs(self) -> dict:
        ret = dict()
        sum_freg = self.root.num
        for k, v in self.root.words.items():
            ret[k] = v / sum_freg
        return ret
