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

from _io import TextIOWrapper


class BaseMorphologicalAnalyser:
    # tokeneknél tok.token-nel hívható
    def tags(self, word: str) -> list:
        ...

    def analyse(self, word: str) -> list:
        ...


class NullAnalyser(BaseMorphologicalAnalyser):
    # todo: Na de hé! Ez kell egyáltalán?
    def tags(self, word):
        return None

    def analyse(self, word):
        return None


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
        return self.morph_table.get(word)  # todo: lehetne itt [] default?

    def analyse(self, word: str):
    # todo: Na de hé! Ez kell egyáltalán?
        return None

