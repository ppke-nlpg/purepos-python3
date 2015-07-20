#!/usr/bin/env Python3
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

from io import TextIOWrapper
from docmodel.token import Token


class BaseMorphologicalAnalyser:
    def tags(self, word: str) -> list:
        pass

    def analyse(self, word: str) -> list:
        pass


class NullAnalyser(BaseMorphologicalAnalyser):
    def tags(self, word: str):
        return []  # eredetileg None

    def analyse(self, word: str):
        return []  # eredetileg None


class MorphologicalTable(BaseMorphologicalAnalyser):
    def __init__(self, file: TextIOWrapper):
        self.morph_file = file
        self.morph_table = {}
        for line in file:
            cells = line.split("\t")
            if len(cells) > 0:
                token = cells[0]
                anals = cells[1:]
                self.morph_table[token] = anals
        file.close()

    def tags(self, word: str):
        return self.morph_table.get(word, [])

    def analyse(self, word: str):
        return []  # eredetileg None


class HumorAnalyser(BaseMorphologicalAnalyser):
    def __init__(self, humor):
        self.humor = humor

    def tags(self, word: str) -> list:
        # return [anal[1] for anal in self.humor.analyze(word)]
        tags = []
        anals = self.humor.analyze(word)
        for anal in anals:
            tags.append(anal[1])
        return tags

    def analyse(self, word: str) -> list:
        tokens = []
        anals = self.humor.analyze(word)
        for anal in anals:
            tokens.append(Token(word, anal[0], anal[1]))
        return tokens
