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

from corpusreader.tokenreaders import BaseReader
from corpusreader.tokenreaders import SentenceReader
from corpusreader.tokenreaders import TaggedTokenReader
from docmodel.containers import Paragraph, Document


class HunPosCorpusReader(BaseReader):
    # Ugyan olyan reader, mint a CorpusReader, csak más a kódolás és a szeparátor.
    # Célszerű lenne úgy refaktorálni, hogy egy paraméterezhető Corpusreader legyen.
    def __init__(self):
        super().__init__(encoding="ISO-8859-2")
        self.word_parser = TaggedTokenReader("\t")
        self.sentence_parser = SentenceReader(self.word_parser, self.linesep)

    def read(self, text: str):
        sentences = list()
        for sent in text.split(self.linesep + self.linesep):
            if len(sent)-1 > 0:
                sentences.append(self.sentence_parser.read(sent))
        paragraph = Paragraph(sentences)
        document = Document()
        document.append(paragraph)
        return document
