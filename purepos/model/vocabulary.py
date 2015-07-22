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

from purepos.model.ngram import NGram


class BiDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.inverse = dict()
        d = dict(*args, **kwargs)
        for k, v in d.items():
            if self.get(k) is None and self.inverse.get(v) is None:
                self[k] = v
                self.inverse[v] = k
            else:
                raise KeyError("BiDict does not allow same values for multiple keys.")

    def __setitem__(self, k, v):
        if "inverse" not in vars(self).keys():
            self.__setattr__("inverse", dict())
        if self.get(k) is None and self.inverse.get(v) is None:
            super().__setitem__(k, v)
            self.inverse[v] = k
        else:
            raise KeyError("BiDict does not allow same values for multiple keys.")

    def __delitem__(self, key):
        v = self.get(key)
        if v is None:
            raise KeyError(key)
        self.inverse.__delitem__(v)
        super().__delitem__(key)


class BaseVocabulary:
    def __init__(self):
        self.voc = BiDict()
        self.max_known_index = None

    def __len__(self):
        return len(self.voc)

    def index(self, word):
        return self.voc.get(word)

    def word(self, index):
        return self.voc.inverse.get(index)

    def indices(self, wlist: list):
        lst = []
        for w in wlist:
            val = self.voc.get(w)
            if val is None:
                return None
            lst.append(val)
        return NGram(lst)

    def add_element(self, element):
        key = self.voc.get(element)
        if key is None:
            return self.add_vocabulary_element(element)
        else:
            return key

    def __str__(self):
        return self.voc.__str__()

    def add_vocabulary_element(self, element):
        pass

    def tag_indices(self):
        return self.voc.values()

    def max_index(self):
        return self.max_known_index

    def store_max_element(self):
        pass


class IntVocabulary(BaseVocabulary):
    def add_vocabulary_element(self, element):
        self.voc[element] = len(self.voc)
        return self.voc[element]

    @staticmethod
    def extremal_element():
        return -1

    def store_max_element(self):
        self.max_known_index = len(self.voc) - 1
