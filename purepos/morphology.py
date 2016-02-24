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

from corpusreader.containers import Token


class Morphology:
    def __init__(self, source=None):
        self.tags = self.morph_table_tags
        self.analyse = self.morph_table_analyse
        if source is None:
            self.anal_source = dict()  # None
        elif isinstance(str, source):
            self.create(source)  # Table
        else:
            self.anal_source = source  # Integrated morphology (any inicialised class with analyse method)
            self.integrated_ma_tags = self.integrated_ma_tags
            self.analyse = self.integrated_ma_analyse

    def create(self, file: str or None):
        if file is not None:
            with open(file, encoding='UTF-8') as f:
                for line in f:
                    cells = line.strip().split('\t')
                    if not line.startswith('#') and len(cells) > 1:  # todo: kivezetni a forátumot...
                        token, anals = cells[0], cells[1:]
                        self.anal_source[token] = anals

    def morph_table_tags(self, word: str):
        return self.anal_source.get(word, [])

    def morph_table_analyse(self, word: str):
        return self.anal_source.get(word, [])

    def integrated_ma_tags(self, word: str) -> list:
        return [anal[1] for anal in self.anal_source.analyze(word)]

    def integrated_ma_analyse(self, word: str) -> list:
        return [Token(word, anal[0], anal[1]) for anal in self.anal_source.analyze(word)]
