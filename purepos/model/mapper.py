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

from purepos.model.vocabulary import IntVocabulary

"""
# StringMapping:
# (tagPattern, replacement)
def stringmapping(pattern: str, replacement: str):
    return re.compile(pattern), replacement
"""

# Ez a fájl sok halott kódot és még több szügségtelen class-t tartalmaz. Ezeket kikommenteltem.
# class BaseMapper:
#     def map(self, element):
#         pass
#
#     def map_list(self, elements: list):
#         pass
#
#
# class BaseTagMapper(BaseMapper):
#     def filter(self, morph_anals: list or set, possible_tags: list or set) -> list:
#         pass


class StringMapper:  # (BaseMapper):
    def __init__(self, mappings: list):
        self.mappings = mappings

    # ok.
    def map(self, element: str):
        return {pattern.sub(replacement, element) for pattern, replacement in self.mappings}

    def map_list(self, elements: list):
        # dead code? But useful. :)
        return [self.map(e) for e in elements]


class TagMapper:  # (BaseTagMapper):
    def __init__(self, tag_vocabulary: IntVocabulary, tag_mappings: list):
        self.vocabulary = tag_vocabulary
        self.tag_mappings = tag_mappings

    def map(self, tag: int) -> int:
        if self.vocabulary.max_index() < tag:
            tag_str = self.vocabulary.word(tag)
            for patt, repl in self.tag_mappings:
                if patt.fullmatch(tag_str):
                    ret_tag = self.vocabulary.index(patt.sub(repl, tag_str))  # Get
                    if ret_tag is not None:
                        return ret_tag
        return tag

    def map_list(self, elements: list):
        return [self.map(e) for e in elements]

    def filter(self, morph_anals: list or set, possible_tags: list or set) -> list:
        # morph_anals megszűrése
        return [anal for anal in morph_anals if self.map(anal) in possible_tags]
