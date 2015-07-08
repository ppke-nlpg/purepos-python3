#!/usr/bin/env Python3
# todo nincs kész
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

from docmodel import token


STEM_FILTER_FILE = "purepos_stems.txt"
STEM_FILTER_PROPERTY = ""  # todo: System.getProperty("stems.path");
UNKOWN_VALUE = -99
LEMMA_MAPPER = None  # todo implement class
analysis_queue = None  # todo implement class and construct an object. Here?
CONFIGURATION = None  # todo implement class and construct an object. Here?


def create_stem_filter():
    raise NotImplementedError()
    # todo: implement at StemFilter


def find_max(d: dict):
    return max(d.values())
    # todo: inline instead of call.
    # maximum = 0.0
    # for v in d.values():
    #     if v > d:
    #         max = v
    # return maximum


def find_max_pair(d: dict):
    max_k = None
    max_v = float("-inf")
    for v in d.values():
        if v[1] > max_v:
            max_k = v[0]
            max_v = v[1]
    return (max_k, max_v)


def add_mappings(comp_modeldata, tag_vocabulary, tag_mappings):
    raise NotImplementedError()
    # todo: implement


def simplify_lemma(t: token.Token):
    if LEMMA_MAPPER is not None:
        return token.ModToken(t.token, stem=LEMMA_MAPPER.map(t.stem), tag=t.tag)
    return t


class BiDict(dict):
    def __init__(self, *args, **kwargs):
        d = dict(*args, **kwargs)
        self.inverse = {}
        for k, v in d.items():
            if self.get(k) is None and self.inverse.get(v) is None:
                self[k] = v
                self.inverse[v] = k
            else:
                raise KeyError("BiDict does not allow same values for multiple keys.")

    def __setitem__(self, k, v):
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

