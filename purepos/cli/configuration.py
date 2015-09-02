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


class Configuration:
    def __init__(self, tag_mappings: list=None,  # stringmapping
                 lemma_mappings: list=None,  # stringmapping
                 guessed_lemma_marker: str="",
                 weight: float=None):
        self.tag_mappings = tag_mappings if tag_mappings is not None else []
        self.lemma_mappings = lemma_mappings if lemma_mappings is not None else []
        self.guessed_lemma_marker = guessed_lemma_marker
        self.weight = weight

    TAG = "to"
    PATTERN = "pattern"
    TAG_MAPPING = "tag_mapping"
    LEMMA_MAPPING = "lemma_mapping"
    GUESSED_MARKER = "guessed_marker"
    SUFFIX_MODEL_PARAMETERS = "suffix_model_weight"

    @staticmethod
    def read(filename: str):
        # todo meg kell csinálni
        raise NotImplementedError("This feature is not (yet) implemented in this version.")
