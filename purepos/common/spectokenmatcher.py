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

import re


class SpecTokenMatcher:
    # Fontos a sorrendtartás, mert az első találatnál megáll a keresés.
    # Semmi szükség példányosításra.
    #
    # @PUNCT rész egészen más eredményt ad, mint a Java implementáció. A Java \pP közel sem
    # tartalmaz minden PUNCT-ot, ezen kívül nem kezeli jól a 4 bájtos karaktereket. A § és a /
    # jelek a Szeged Corpus konvenciói miatt itt NEM részei a @PUNCT halmaznak.
    # <megj.> A ` karakter egyszer fordul elő a Szeged általunk használt verziójában,
    # ott is véletlen szemét.</megj.>
    cls_pat_list = [
        ("@CARD", re.compile("^[0-9]+$")),
        ("@CARDPUNCT", re.compile("^[0-9]+\.$")),
        ("@CARDSEPS", re.compile("^[0-9\.,:\-]+[0-9]+$")),
        ("@CARDSUFFIX", re.compile("^[0-9]+[a-zA-Z][a-zA-Z]?[a-zA-Z]?$")),
        ("@HTMLENTITY", re.compile("^&[^;]+;?$")),
        ("@PUNCT", re.compile('^['+re.escape(u'!"#$%&()*+,-.:;<=>?@[\]^_`{|}~«»…·→—•\'')+']+$'),
         re.U)
    ]

    @staticmethod
    def match_lexical_element(token: str):
        for pair in SpecTokenMatcher.cls_pat_list:
            if pair[1].match(token):
                return pair[0]
        return None
