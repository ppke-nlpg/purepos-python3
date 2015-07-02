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

import _io
from docmodel.token import Token
from docmodel.containers import Sentence


class ParsingException(Exception):
    pass


class BaseReader:
    def __init__(self, separator: str="#"):
        self.separator = separator
        self.linesep = "\n"
        self.encoding = "UTF-8"

    def read(self, text: str):
        ...

    def read_from_file(self, file: _io.TextIOWrapper):
        # todo: Biztos jó ötlet az egész fájlt beolvasni? Esetleg yield?
        # todo: itt kéne az encoding-ot használni. Kell?
        return self.read(file.read())
    # todo: Ez nem kell Pythonba.
    # todo: line separator
    # def read_from_scanner(self, scanner):
    #     def read_scanner(sc):
    #
    #         pass
    #
    #     return self.read(read_scanner(scanner))


class SimpleTokenReader(BaseReader):
    def read(self, text: str):
        return Token(text)


class TaggedTokenReader(BaseReader):
    def read(self, text: str):
        w_parts = text.split(self.separator)
        if len(w_parts) != 2:
            raise ParsingException("Malformed input: '{}'".format(text))
        return Token(w_parts[0], w_parts[1])


class StemmedTaggedTokenReader(BaseReader):
    def read(self, text: str):
        w_parts = text.split(self.separator)
        if len(w_parts) < 3:  # todo: 3-nál hosszabb lehet?
            raise ParsingException("Malformed input: '{}'".format(text))
        return Token(w_parts[0], w_parts[2], w_parts[1].replace('_', ' '))


class SentenceReader(BaseReader):
    def __init__(self, word_parser: BaseReader, separator: str="\s"):
        super().__init__(separator)
        self.word_parser = word_parser

    def read(self, text: str):
        if not text:
            return Sentence()
        tokens = Sentence()
        for word in text.split(self.separator):
            if len(word) == 0:
                raise ParsingException("Empty word in '{}'".format(text))
            # token = self.word_parser.read(word)
            # if token is not None:  # todo: token lehet none? Ha nem, nem kell None check.
            #     tokens.append(token)
            tokens.append(self.word_parser.read(word))
        return tokens









