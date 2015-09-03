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
    # Mappingek konfigurálása külső, XML fájlon keresztül.
    # Hasznos lenne átgondolni, ill. see more:
    # https://github.com/ppke-nlpg/purepos-python3/issues/7
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
        # XML fájlból Configuration beparszolása.
        from xml.etree import ElementTree
        from purepos.model.mapper import stringmapping
        root = ElementTree.parse(filename).getroot()
        tag_mapping_elements = root.findall(Configuration.TAG_MAPPING)
        tag_mappings = []
        for tm in tag_mapping_elements:
            spat = tm.attrib[Configuration.PATTERN]
            stag = tm.attrib[Configuration.TAG]
            tag_mappings.append(stringmapping(spat, stag))

        lemma_mapping_elements = root.findall(Configuration.LEMMA_MAPPING)
        lemma_mappings = []
        for lm in lemma_mapping_elements:
            spat = lm.attrib[Configuration.PATTERN]
            stag = lm.attrib[Configuration.TAG]
            lemma_mappings.append(stringmapping(spat, stag))

        marker_elements = root.findall(Configuration.GUESSED_MARKER)
        guessed_marker = marker_elements[0].text if len(marker_elements) > 0 else ""

        param_elements = root.findall(Configuration.SUFFIX_MODEL_PARAMETERS)
        weight = float(param_elements[0].text) if len(param_elements) > 0 else None

        return Configuration(tag_mappings, lemma_mappings, guessed_marker, weight)
