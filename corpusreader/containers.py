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

from purepos.common.util import LEMMA_MAPPER


class Colors:
    SEPARATOR = ""
    WORD = ""
    LEMMA = ""
    TAGS = ""
    ENDC = ""


class Token:
    """Class representing a stemmed tagged token in a sentence."""
    SEP = "#"

    def __init__(self, token: str, stem: str=None, tag: str=None):
        self.token = token
        self.stem = stem
        self.original_stem = None
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

    def simplify_lemma(self):
        if LEMMA_MAPPER is not None:
            self.original_stem = self.stem
            self.stem = LEMMA_MAPPER.map(self.stem)
        return self
