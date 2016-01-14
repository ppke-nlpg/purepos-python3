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


class Colors:
    SEPARATOR = ""
    WORD = ""
    LEMMA = ""
    TAGS = ""
    ENDC = ""


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


class Paragraph(list):
    """Represents a parapraph of tagged, stemmed sentences."""

    def __init__(self, *sentences):
        super().__init__(*sentences)

    def __str__(self):
        return NL.join([str(x) for x in self])


class Sentence(list):
    """Represents a POS-tagged stemmed sentence."""

    def __init__(self, *tokens, score=None):
        super().__init__(*tokens)
        self.score = score

    def __str__(self):
        return SENTENCE_SEP.join([str(x) for x in self])


class Token:
    """Class representing a stemmed tagged token in a sentence."""
    SEP = "#"

    def __init__(self, token: str, stem: str=None, tag: str=None):
        self.token = token
        self.stem = stem
        self.tag = tag
        # Unique hash cached for faster access
        self.hash_code = hash((self.stem, self.tag, self.token))

    def __str__(self):
        if self.tag is not None and self.stem is None:
            return Colors.WORD + self.token + Colors.SEPARATOR + self.SEP + \
                Colors.TAGS + self.tag + Colors.ENDC
        else:
            return Colors.WORD + self.token + Colors.SEPARATOR + self.SEP + Colors.LEMMA + \
                self.stem + Colors.SEPARATOR + self.SEP + Colors.TAGS + self.tag + Colors.ENDC

    def __hash__(self):
        return self.hash_code

    def __eq__(self, other):
        """
        if other is not None and isinstance(other, Token):
            return (other.token == self.token) and\
                   (other.stem == self.stem) and \
                   (other.tag == self.tag)
        else:
            return False
        """
        """
        Hashable objects which compare equal must have the same hash value.
        All of Python’s immutable built-in objects are hashable, while no mutable containers
        (such as lists or dictionaries) are. Objects which are instances of user-defined classes are hashable
        by default; they all compare unequal (except with themselves), and their hash value is derived from their id().
        Source: https://docs.python.org/3/glossary.html#term-hashable
        """
        return isinstance(other, Token) and self.__hash__() == other.__hash__()


class ModToken(Token):
    # Érdemes átgondolni, hogy kell-e erre egy külön osztály
    def __init__(self, token: str, original_stem: str=None, stem: str=None, tag: str=None):
        self.original_stem = original_stem
        super().__init__(token, stem, tag)
