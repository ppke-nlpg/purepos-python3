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

from purepos.common.corpusrepresentation import Token
from purepos.model.vocabulary import IntVocabulary


# This algorithm has O(n^2) complexity!
def full_transformation(word, lemma):
    word_lemma = longest_substring(word, lemma)
    lemma_word = longest_substring(lemma, word)
    remove_start = word_lemma[0]
    remove_end = len(word) - (word_lemma[0] + word_lemma[1])
    add_start = lemma[0:lemma_word[0]]
    add_end = lemma[lemma_word[0] + lemma_word[1]:]

    return remove_start, remove_end, add_start, add_end


# This algorithm has O(n) complexity!
def suffix_transformation(word, lemma):
    i = 0
    while i < min(len(word), len(lemma)):
        if word[i] != lemma[i]:
            break
        i += 1
    word_suff = word[i:]
    remove_start = 0
    remove_end = len(word) - len(word_suff)
    add_start = ''
    add_end = lemma[i:]

    return remove_start, remove_end, add_start, add_end


def longest_substring(s1: str, s2: str) -> tuple:
    """
    Calculates the longest substring efficiently.
    Source: https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Longest_common_substring#Python3
    :param s1:
    :param s2:
    :return: start position and length
    """
    m = [[0] * (1 + len(s2)) for _ in range(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in range(1, 1 + len(s1)):
        for y in range(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return x_longest - longest, longest


class LemmaTransformation:  # todo: Make wire out transformation selection to the configuration
    def __init__(self, word: str, lemma: str, tag: int, transformation=suffix_transformation):  # Decode
        """
        Bug in PurePOS: If a word case differs from its lemmas case (start of a sentence)
        it won't be included in the freq_table! (Fixed!) eg. Éves#éves#MN.NOM
        :param word: word
        :param lemma: lemma
        :param tag: label
        :return: decoded to our representation
        """
        self.lowered = False  # is lowered?
        self.uppered = False  # is uppered?
        self.l = '-'
        if len(word) > 0 and len(lemma) > 0:
            self.lowered = word[0].isupper() and lemma[0].islower()  # Budapesti -> budapesti (at the begin of sentence)
            self.uppered = word[0].islower() and lemma[0].isupper()  # budapesti -> Budapest
            if self.lowered:
                self.l = '_'
                lemma = lemma[0].upper() + lemma[1:]  # Prevent redundancy in the transformation...
            elif self.uppered:
                self.l = '^'
                lemma = lemma[0].lower() + lemma[1:]

        self.remove_start, self.remove_end, self.add_start, self.add_end = transformation(word, lemma)
        self.tag = tag
        self.str_rep = '({0},< -{1}+\'{2}\', >-{3}+\'{4}\' -{5})'.format(self.l, self.remove_start, self.add_start,
                                                                         self.remove_end, self.add_end, self.tag)
        self.hash_code = hash(self.str_rep)

    def __str__(self):
        return self.str_rep

    def __hash__(self):
        return self.hash_code

    def __eq__(self, other):
        """
        Hashable objects which compare equal must have the same hash value.
        All of Python’s immutable built-in objects are hashable, while no mutable containers
        (such as lists or dictionaries) are. Objects which are instances of user-defined classes are hashable
        by default; they all compare unequal (except with themselves), and their hash value is derived from their id().
        Source: https://docs.python.org/3/glossary.html#term-hashable
        """
        return isinstance(other, type(self)) and self.__hash__() == other.__hash__()

    def min_cut_length(self) -> int:
        return self.remove_end

    def encode(self, word: str, vocab: IntVocabulary) -> Token:
        sub_end = max(0, len(word) - self.remove_end)
        lemma = word[0:sub_end] + self.add_end
        lemma = (self.add_start + lemma[min(self.remove_start, len(lemma)):])
        if len(word) > 0 and word[0] != word[0].lower() and self.lowered and len(lemma) > 0:
            lemma = lemma[0].lower() + lemma[1:]
        elif len(word) > 0 and word[0] != word[0].upper() and self.uppered and len(lemma) > 0:
            lemma = lemma[0].upper() + lemma[1:]
        return Token(word, lemma, vocab.word(self.tag))
