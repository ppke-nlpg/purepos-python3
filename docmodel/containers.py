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

SENTENCE_SEP = " "
NL = os.linesep


class Sentence(list):
    """Represents a POS-tagged stemmed sentence."""

    def __init__(self, *tokens, score=None):
        super().__init__(*tokens)
        self.score = score

    def __str__(self):
        return SENTENCE_SEP.join([str(x) for x in self])


class Paragraph(list):
    """Represents a parapraph of tagged, stemmed sentences."""

    def __init__(self, *sentences):
        super().__init__(*sentences)

    def __str__(self):
        return NL.join([str(x) for x in self])


class Document(list):
    """Represents a document object which are built of paragraphes."""

    def __init__(self, *paragraphes):
        super().__init__(*paragraphes)

    def __str__(self):
        return NL.join([str(x) for x in self])

    def sentences(self):
        ret = []
        for p in self:
            ret.extend(p)
        return ret
