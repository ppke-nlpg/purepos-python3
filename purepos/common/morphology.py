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

from purepos.common.corpusrepresentation import Token
from purepos.configuration import Configuration


class Morphology:
    def __init__(self, conf: Configuration, source=None):
        self.conf = conf
        if source is None:
            self.anal_source = dict()  # None
        elif isinstance(source, str):
            self.create(source)  # Table
        else:
            self.anal_source = source  # Integrated morphology (any inicialised class with analyse method)
            self.anal_source.get = lambda x, _: self.anal_source.stem(x)

    def create(self, file: str or None):
        if file is not None:
            with open(file, encoding='UTF-8') as f:
                for line in f:
                    cells = line.strip().split('\t')
                    if not line.startswith(self.conf.COMMENT) and len(cells) > 1:
                        token, anals = cells[0], cells[1:]           # todo: Csak taggelés esetén is működjön!
                        self.anal_source[token] = [anal.split() for anal in anals]

    def tags(self, word: str):
        return [anal[1] for anal in self.anal_source.get(word, [])]

    def analyse(self, word: str, tag: str):
        return [Token(word, anal[0], anal[1]) for anal in self.anal_source.get(word, []) if len(anal) > 0 and
                anal[1] == tag]
