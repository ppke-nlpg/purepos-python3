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

import os
from docmodel import token
from purepos.common.analysisqueue import AnalysisQueue

STEM_FILTER_FILE = "purepos_stems.txt"
UNKOWN_VALUE = -99.0
LEMMA_MAPPER = None  # StringMapper
analysis_queue = AnalysisQueue()
CONFIGURATION = None  # Nem teszteltük.


class Constants:  # todo: ötlet minden konstan egy objektumba -> egy időben több különböző PurePOS
    # todo: https://github.com/ppke-nlpg/purepos-python3/issues/7
    def __init__(self):
        pass

class StemFilter:
    def __init__(self, filename: str):
        self.stems = set()
        with open(filename) as file:
            self.stems = set(file.readlines())

    def filter_stem(self, candidates) -> list:
        if len(self.stems) == 0:
            return candidates
        ret = []
        for t in candidates:
            if t.stem in self.stems:
                ret.append(t)
        if len(ret) == 0:
            return candidates
        return ret

    @staticmethod
    def create_stem_filter():
        # Régi örökség, de jó ha van. Lásd: Obamának -> Obama, Obamá, Obam
        if os.path.isfile(STEM_FILTER_FILE):
            return StemFilter(STEM_FILTER_FILE)


# Inlined everywhere.
# def find_max(d: dict) -> tuple:  # {key: value}
#     return max(d.items(), key=lambda e: e[1])  # select the value of order key.


# def find_max_pair(d: dict) -> tuple:  # {key: (bármi, float)}
#     t = max(d.items(), key=lambda e: e[1][1])
#     return t[0], t[1][1]
    # max_k = None
    # max_v = float("-inf")
    # for key, pair in d.items():
    #     if pair[1] > max_v:
    #         max_k = key
    #         max_v = pair[1]
    # return max_k, max_v


def simplify_lemma(t: token.Token):
    if LEMMA_MAPPER is not None:
        return token.ModToken(t.token, original_stem=t.stem,
                              stem=LEMMA_MAPPER.map(t.stem), tag=t.tag)
    return t
