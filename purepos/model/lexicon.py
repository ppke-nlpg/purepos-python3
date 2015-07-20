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


class Lexicon:
    def __init__(self):
        self.representation = {}
        self.size = 0

    def add_token(self, token, tag):
        if token in self.representation:
            value = self.representation[token]
            if tag in value:
                value[tag] += 1
            else:
                value[tag] = 1
        else:
            self.representation[token] = {tag, 1}
        self.size += 1

    def tags(self, word) -> set:
        return set(self.representation.get(word, {}).keys())

    def word_count(self, word) -> int:
        total = 0
        for c in self.representation.get(word, {}).values():
            total += c
        return total

    # todo: iterátor. egészen pontosan min kell végigmenni?
    def iterator(self):
        return self.representation.items()

    def wordcount_for_tag(self, word, tag):
        return self.representation.get(word, {}).get(tag, 0)
