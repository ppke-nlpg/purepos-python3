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
# from purepos.model.compiledmodeldata import CompiledModelData
# from purepos.model.mapper import TagMapper
# from purepos.model.vocabulary import BaseVocabulary
from purepos.decoder.stemfilter import StemFilter


STEM_FILTER_FILE = "purepos_stems.txt"  # todo: be kell égetni?
STEM_FILTER_PROPERTY = ""  # todo: System.getProperty("stems.path");
UNKOWN_VALUE = -99.0
LEMMA_MAPPER = None  # StringMapper
analysis_queue = AnalysisQueue()
CONFIGURATION = None


class Constants:  # todo: ötlet minden konstan egy objektumba -> egy időben több különböző PurePOS
    def __init__(self):
        pass


def create_stem_filter() -> StemFilter:
    path = None
    if STEM_FILTER_PROPERTY and os.path.isfile(STEM_FILTER_PROPERTY):
        path = os.path.abspath(STEM_FILTER_PROPERTY)

    if os.path.isfile(STEM_FILTER_FILE):
        path = os.path.abspath(STEM_FILTER_FILE)
    # todo: ezt végképp nem értem!!!

    if path is None:
        return None
    return StemFilter(path)


def find_max(d: dict) -> tuple:
    return max(d.items(), key=lambda e: e[1])  # select the value of order key.


def find_max_pair(d: dict) -> tuple:  # {key: (v, float)}
    max_k = None
    max_v = float("-inf")
    for key, pair in d.items():
        if pair[1] > max_v:
            max_k = key
            max_v = pair[1]
    return max_k, max_v


def smooth(val: float):
    if val is not None and val != float("-inf"):
        return val
    else:
        return UNKOWN_VALUE


# átkerült a compiled_model_datába
# def add_mappings(comp_modeldata: CompiledModelData,
#                  tag_vocabulary: BaseVocabulary,
#                  tag_mappings: list):
#     mapper = TagMapper(tag_vocabulary, tag_mappings)
#     comp_modeldata.standard_emission_model.context_mapper = mapper
#     comp_modeldata.spec_tokens_emission_model.context_mapper = mapper
#     comp_modeldata.tag_transition_model.context_mapper = mapper
#     comp_modeldata.tag_transition_model.element_mapper = mapper
#     comp_modeldata.lower_case_suffix_guesser.tag_mapper = mapper
#     comp_modeldata.upper_case_suffix_guesser.tag_mapper = mapper

# ok.
def simplify_lemma(t: token.Token):
    if LEMMA_MAPPER is not None:
        return token.ModToken(t.token, original_stem=t.stem,
                              stem=LEMMA_MAPPER.map(t.stem), tag=t.tag)
    return t
