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
        return "(id: {}, words: {})".format(self.id_, str(self.words))
