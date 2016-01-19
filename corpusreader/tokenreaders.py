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

import io
import os
import sys
from corpusreader.containers import Document, Paragraph, Sentence, Token


class ParsingException(Exception):
    pass


# todo: Be mor Pyhthonic use indices where it possible to avoid string copiing...
class CorpusReader:
    def __init__(self, field_sep: str='#', token_sep: str=' ', sentence_sep: str=os.linesep,
                 para_sep: str=os.linesep+os.linesep, encoding='UTF-8'):
        self.field_sep = field_sep
        self.token_sep = token_sep
        self.sentence_sep = sentence_sep
        self.para_sep = para_sep
        self.encoding = encoding

    def read_from_io(self, file: io.TextIOWrapper):
        # Reads the entire file into memory because it must be read more than one times!
        return self.read_corpus(file.read())

    def read_corpus(self, text: str):
        # it parses the whole(!) analysed corpus
        document = Document()
        # XXX Ony one pararaph at the moment
        # for paragraph in text.split(self.para_sep):
        paragraph = text.rstrip(self.sentence_sep)  # After the last sentence there is nothing
        if len(paragraph) == 0:
            raise ParsingException("Empty paragraph in '{}'".format(text))
        document.append(self.read_paragraph(paragraph))
        return document

    def read_paragraph(self, text: str):
        paragraph = Paragraph()
        sentenes = text.split(self.sentence_sep)
        for sentence in sentenes:
            if len(sentence) == 0:
                raise ParsingException("Empty sentence in '{}'".format(text))
            try:
                paragraph.append(self.read_sentence(sentence))
            except ParsingException as ex:
                print("{}\nWARNING: Skipping sentence!".format(print(ex)), file=sys.stderr)
        return paragraph

    def read_sentence(self, text: str):
        sentence = Sentence()
        for word in text.split(self.token_sep):
            if len(word) == 0:
                raise ParsingException("Empty word in '{}'".format(text))
            sentence.append(self.read_token(word))
        return sentence

    def read_token(self, text: str):
        w_parts = text.split(self.field_sep)
        if len(w_parts) != 3:
            raise ParsingException("Malformed input: '{}'".format(text))
        return Token(w_parts[0], w_parts[1].replace('_', ' '), w_parts[2])
