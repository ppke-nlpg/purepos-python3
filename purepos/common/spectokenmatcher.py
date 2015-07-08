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

import re


class SpecTokenMatcher:
    def __init__(self):
        self.patterns = {}
        self.patterns["@CARD"] = re.compile("^[0-9]+$")
        self.patterns["@CARDPUNCT"] = re.compile("^[0-9]+\\.$")
        self.patterns["@CARDSEPS"] = re.compile("^[0-9\\.,:-]+[0-9]+$")
        self.patterns["@CARDSUFFIX"] = re.compile("^[0-9]+[a-zA-Z][a-zA-Z]?[a-zA-Z]?$")
        self.patterns["@HTMLENTITY"] = re.compile("^&[^;]+;?$")
        # self.patterns["@PUNCT"] = re.compile("^\\pP+$")
        self.patterns["@PUNCT"] = \
            re.compile('^['+re.escape('!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~')+']+$')
# todo ellenőrizni

    def match_lexical_element(self, token: str):
        for k, v in self.patterns.items():
            if v.match(token):
                return k
        return None
