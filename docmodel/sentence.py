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

import os

SENTENCE_SEP = " "
NL = os.linesep

class Sentence(list):
    """Represents a POS-tagged stemmed sentence."""

    def __init__(self, tokens):
        super().__init__(tokens)
        self.score = None

    def __str__(self):
        return SENTENCE_SEP.join([str(x) for x in self])

    # Nem kell, mert a list tartalmazza.
    # def __eq__(self, other):
    #     if other is not None and isinstance(other, Sentence):
    #         return len(self) == len(other) and
    #     else:
    #         return False

