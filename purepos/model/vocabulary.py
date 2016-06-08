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
from collections import Counter, defaultdict


class BiDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inverse = {v: k for k, v in self.items()}
        if len(self) != len(self.inverse):
            raise KeyError("BiDict does not allow same values for multiple keys.")

    def __setitem__(self, k, v):
        if "inverse" not in vars(self).keys():
            self.__setattr__("inverse", dict())
        if self.__contains__(k) or v in self.inverse:
            raise KeyError("BiDict does not allow same values for multiple keys.")
        else:
            super().__setitem__(k, v)
            self.inverse[v] = k

    def setdefault(self, k, v=None):
        # Here this is enough because __setitem__() take care of everything else
        if not self.__contains__(k):
            self.__setitem__(k, v)
            return v
        return self.__getitem__(k)

    def __delitem__(self, key):
        v = self.__getitem__(key)
        self.inverse.__delitem__(v)
        super().__delitem__(key)


class Lexicon:
    def __init__(self):
        self.representation = defaultdict(Counter)
        self.size = 0

    def add_token(self, token, tag):
        self.representation[token][tag] += 1
        self.size += 1

    def tags(self, word) -> set:
        return set(self.representation[word].keys())

    def word_count(self, word) -> int:
        return sum(c for c in self.representation[word].values())

    def items(self):
        return self.representation.items()

    def wordcount_for_tag(self, word, tag):
        return self.representation[word][tag]

    def keys(self):
        return self.representation.keys()

    def get_all(self, word):
        return self.representation[word]


class IntVocabulary(BiDict):
    def __init__(self, *args, **kwargs):
        self.max_known_index = None
        super().__init__(*args, **kwargs)

    # Should not give None
    def index(self, word):
        return self.__getitem__(word)

    def word(self, index):
        return self.inverse[index]

    def add_element(self, element):
        return self.setdefault(element, self.__len__())

    def tag_indices(self):
        return self.values()

    def max_index(self):
        return self.max_known_index

    @staticmethod
    def extremal_element():
        return -1

    def store_max_element(self):
        self.max_known_index = self.__len__() - 1


class LemmaUnigramModel(Counter):
    """We use the feature of Counter class, that it gives 0 as default value instead of None.
    The rest is just counting elements as a dict."""

    @classmethod
    def fromkeys(cls, iterable, v=None):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def log_prob(self, key, unk_value):
        prob = self.__getitem__(key) / self.__len__()
        return math.log(prob) if prob > 0 else unk_value


class TrieNode:
    def __init__(self, _id, word=None, node_type=int):
        self.id_ = _id
        self.words = dict()
        self.child_nodes = dict()
        self.node_type = node_type
        self.num = self.zero()

        if word is not None:
            self.add_word(word)

    def zero(self):
        return self.node_type(0)

    def increment(self, num):
        return num + self.node_type(1)

    def create_node(self, _id):
        return TrieNode(_id, node_type=self.node_type)

    def add_word(self, word):
        if word in self.words.keys():
            self.words[word] = self.increment(self.words[word])
        else:
            self.words[word] = self.increment(self.zero())
        self.num = self.increment(self.num)

    def add_child(self, child):
        if child not in self.child_nodes.keys():
            child_node = self.create_node(child)
            self.child_nodes[child] = child_node
            return child_node
        return self.child_nodes[child]

    def apriori_prob(self, word) -> float:
        if word in self.words.keys():
            return self.words[word] / self.num
        else:
            return 0.0

    def __str__(self):
        return '(id: {}, words: {})'.format(self.id_, str(self.words))
