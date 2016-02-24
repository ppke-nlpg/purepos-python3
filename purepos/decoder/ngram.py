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


class NGram:
    def __init__(self, tokens: list, compare_length: int=-1, new_element=None):
        self.token_list = tokens
        self.compare_length = compare_length
        if new_element is not None:
            l = list(tokens)
            l.append(new_element)
            self.token_list = l
        self.hash = self.init_hash()

    def add(self, element):
        return NGram(self.token_list, self.compare_length, element)

    def __str__(self):
        return str(self.token_list)

    def __hash__(self):
        return self.hash

    def init_hash(self) -> int:
        # Ennek a célja, hogy a hash kódot előre legyártsa, mert nagyon gyakran lesz rá szükség.
        s = 0
        if self.compare_length != -1:
            size = self.compare_length
        else:
            size = float("inf")
        c = 0
        for tok in self.token_list[::-1]:
            if c >= size:
                break
            s += tok*31  # prím szám.
            c += 1
        return s

    def __eq__(self, other):
        # Az azonosságvizsgálatnál csak az utolsó n token(tag-e)-t vizsgáljuk
        return self.token_list[-self.compare_length:] == other.token_list[-self.compare_length:]

    def last(self):
        return self.token_list[-1]


class Node:
    def __init__(self, state: NGram, weight: float, previous: NGram or None):
        self.state = state
        self.weight = weight
        self.prev = previous

    def __str__(self):
        return "{state: {}, weight: {}}".format(str(self.state), str(self.weight))
