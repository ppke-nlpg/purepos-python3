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
from corpusreader.tokenreaders import BaseReader
from corpusreader.tokenreaders import SentenceReader
from docmodel.containers import Paragraph, Document


class CorpusReader(BaseReader):
    def __init__(self, token_reader: BaseReader, linesep: str=os.linesep):
        super().__init__(linesep=linesep)
        self.token_reader = token_reader
        self.sentence_parser = SentenceReader(self.token_reader)

    def read(self, text: str):
        # it parses the whole(!) analysed corpus
        sentences = list()
        for line in text.split(self.linesep):
            if len(line) > 0:
                sentences.append(self.sentence_parser.read(line))
        paragraph = Paragraph(sentences)
        document = Document()
        document.append(paragraph)
        return document
