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
from corpusreader.containers import Token


class ParsingException(Exception):
    pass

def find_all(a_str, sub):
    """
    Original Source: http://stackoverflow.com/a/4665027
    """
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1:
            yield None   # Slice at the end
            return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches


class CorpusReader:
    def __init__(self, field_sep: str='#', token_sep: str=' ', sentence_sep: str=os.linesep,
                 para_sep: str=os.linesep+os.linesep, encoding='UTF-8'):
        self.field_sep = field_sep
        self.token_sep = token_sep
        self.sentence_sep = sentence_sep
        self.para_sep = para_sep
        self.encoding = encoding

    def read_from_io(self, fileh: io.TextIOWrapper):
        # Reads the entire file into memory because it must be read more than one times!
        return self.read_corpus(fileh.read())

    def read_corpus(self, text: str):
        """
        Parses the whole(!) analysed corpus
        :param text: the whole corpus
        :return: lists embeded lists embeded...

        """
        # Strip last separators...
        if text.endswith(self.para_sep):
            text = text[:-len(self.para_sep)]
        if text.endswith(self.sentence_sep):
            text = text[:-len(self.sentence_sep)]
        if text.endswith(self.token_sep):
            text = text[:-len(self.token_sep)]

        doc = []
        para_start = -1
        for para_end in find_all(text, self.para_sep):
            para = text[slice(para_start + 1, para_end)]  # No need to check for None ;)
            sent_start = -1
            para_sents = []
            for sent_end in find_all(para, self.sentence_sep):
                sent = para[slice(sent_start + 1, sent_end)]  # No need to check for None ;)
                tok_start = -1
                sent_toks = []
                try:
                    for tok_end in find_all(sent, self.token_sep):
                        tok = sent[slice(tok_start + 1, tok_end)]  # No need to check for None ;)
                        try:
                            word, lemma, pos = tok.split(self.field_sep)
                        except ValueError:
                            raise ParsingException("Malformed input: '{}'".format(tok))
                        sent_toks.append(Token(word, lemma.replace('_', ' '), pos))
                        tok_start = tok_end
                except ParsingError as ex:
                    print(ex, 'WARNING: Skipping sentence!', sep=os.linesep, file=sys.stderr)
                sent_start = sent_end
                para_sents.append(sent_toks)
            para_start = para_end
            doc.append(para_sents)
        return doc
