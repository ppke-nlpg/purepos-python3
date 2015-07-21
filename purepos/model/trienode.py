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


# todo nagyon nagyon jávás megközelítés.
class BaseTrieNode:
    def __init__(self, _id, word=None):
        self.id_ = _id
        self.words = dict()
        self.num = self.zero()
        self.child_nodes = dict()

        if word is not None:
            self.add_word(word)

    def zero(self):
        pass

    def increment(self, num):
        pass

    def create_node(self, _id):
        pass

    def add_word(self, word):
        if word in self.words.keys():
            self.words[word] = self.increment(self.words[word])
        else:
            self.words[word] = self.increment(self.zero())
        self.increment(self.num)

    def add_child(self, child):
        if child not in self.child_nodes.keys():
            child_node = self.create_node(child)
            self.child_nodes[child] = child_node
            return child_node
        return self.child_nodes[child]

    # todo inline?
    def has_child(self, _id) -> bool:
        return _id in self.child_nodes.keys()

    # todo inline!
    def get_child(self, _id):
        return self.child_nodes.get(_id)

    # todo inline?
    def has_word(self, word) -> bool:
        return word in self.words.keys()

    # todo inline!
    def get_word(self, word):
        return self.words.get(word)

    def __str__(self):
        return "(id: {}, words: {})".format(self.id_, str(self.words))

    # todo: getReprString csak ha kell.


class IntTrieNode(BaseTrieNode):
    def __init__(self, _id, word=None):
        super().__init__(_id, word)

    def zero(self) -> int:
        return 0

    def increment(self, num) -> int:
        return num + 1

    def create_node(self, _id):
        return IntTrieNode(_id)

    def apriori_prob(self, word) -> float:
        if word in self.words.keys():
            return self.words[word] / self.num
        else:
            return 0.0


# todo: DoubleTrieNode
class FloatTrieNode(BaseTrieNode):
    def __init__(self, _id, word=None):
        super().__init__(_id, word)

    def zero(self) -> int:
        return 0.0

    def increment(self, num) -> int:
        return num + 1.0

    def create_node(self, _id):
        return FloatTrieNode(_id)

    # todo inline?
    def add_word_prob(self, word, prob: float):
        self.words[word] = prob

    # todo ez nem valódi leszármazott, mást csinál!
    # todo ezért INLINE!!!
    def add_child(self, child):
        self.child_nodes[child.id_] = child
        raise Warning("Ezt a függvényt ne hívd meg! Inlájnold!")
