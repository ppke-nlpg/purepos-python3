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

from docmodel.token import Token
from purepos.model.vocabulary import BaseVocabulary
from purepos.model.modeldata import ModelData


def def_lemma_representation(word, stem, tag):
    return SuffixLemmaTransformation(word, stem, tag)


def def_lemma_representation_by_token(token: Token, data: ModelData):
    return def_lemma_representation(token.token, token.stem, data.tag_vocabulary.index(token.tag))


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


def lower_transformed(word: str, lemma: str) -> bool:
    if len(word) > 0 and len(lemma) > 0:
        return word[0].isupper() and lemma[0].islower()
    return False


class BaseLemmaTransformation:
    def __init__(self, word: str, lemma: str, tag: int):
        self.representation = self.decode(word, lemma, tag)

    def analyse(self, word) -> tuple:
        encoded = self.encode(word, self.representation)
        # return encoded[0], encoded[1]
        # Gyuri hack a kötőjeles lemmák elkerüléséért.
        return self.__postprocess(encoded[0]), encoded[1]

    def convert(self, word: str, vocab: BaseVocabulary) -> Token:
        anal = self.analyse(word)       # (str, int)
        tag = vocab.word(anal[1])       # str
        return Token(word, anal[0], tag)

    def __str__(self) -> str:
        return str(self.representation)

    def __hash__(self):
        return self.representation.__hash__()

    def __eq__(self, other) -> bool:
        return isinstance(other, type(self)) and self.representation == other.representation

    def min_cut_length(self) -> int:
        pass

    def decode(self, word: str, lemma: str, tag: int):
        pass

    def encode(self, word: str, rep) -> tuple:
        pass

    @staticmethod
    def __postprocess(lemma: str) -> str:
        # Lemma végi „-” leszedése.
        # pl.: Delacroix-é -> Delacroix-[FN][POS][NOM] -> Delacroix
        if len(lemma) > 1 and lemma[-1] == '-':
            return lemma[:-1]
        return lemma
        # return lemma.rstrip('-', )

    @staticmethod
    def token(word: str, lemma: str, tag: str) -> Token:
        return Token(word, lemma, tag)


class Transformation:
    def __init__(self, rem_start: int, rem_end: int, add_start: str, add_end: str, tag: int, lowered: bool):
        self.remove_start = rem_start
        self.remove_end = rem_end
        self.add_start = add_start
        self.add_end = add_end
        self.tag = tag
        self.lowered = lowered
        l = "_" if self.lowered else "-"
        self.str_rep = "({0},< -{1}+\'{2}\', >-{3}+\'{4}\' -{5})".format(l, rem_start, add_start, rem_end, add_end, tag)
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
        return isinstance(other, Transformation) and self.__hash__() == other.__hash__()


class GeneralizedLemmaTransformation(BaseLemmaTransformation):
    def __init__(self, word: str, lemma: str, tag: int):
        super().__init__(word, lemma, tag)

    def min_cut_length(self) -> int:
        return self.representation.remove_end

    def decode(self, word: str, lemma: str, tag: int) -> Transformation:
        """
        XXX Fails on budapesti -> Budapest
        :param word: word
        :param lemma: lemma
        :param tag: label
        :return: decoded to our representation
        """
        pos_word_lemma = longest_substring(word, lemma)
        pos_lemma_word = longest_substring(lemma, word)

        lowered = False  # is lowered?
        if len(word) > 0 and len(lemma) > 0:
            lowered = word[0].isupper() and lemma[0].islower()

        remove_start = pos_word_lemma[0]
        remove_end = len(word) - (pos_word_lemma[0] + pos_word_lemma[1])
        add_start = lemma[0:pos_lemma_word[0]]
        add_end = lemma[pos_lemma_word[0] + pos_lemma_word[1]:]
        return Transformation(remove_start, remove_end, add_start, add_end, tag, lowered)

    def encode(self, word: str, rep: Transformation) -> tuple:
        sub_end = max(0, len(word) - rep.remove_end)
        lemma = word[0:sub_end] + rep.add_end
        lemma = (rep.add_start + lemma[min(rep.remove_start, len(lemma)):]).lower()
        if word != word.lower() and not rep.lowered and len(lemma) > 0:
            lemma = lemma[0].upper() + lemma[1:]
        return lemma, rep.tag


class SuffixLemmaTransformation(BaseLemmaTransformation):
    def __init__(self, word: str, lemma: str, tag: int):
        self._SHIFT = 100
        super().__init__(word, lemma, tag)

    def min_cut_length(self):
        return self.representation[1] % self._SHIFT

    def decode(self, word: str, stem: str, tag: int) -> tuple:
        i = 0
        word_len = len(word)
        end = min(word_len, len(stem))
        while i < end and word[i] == stem[i]:
            i += 1
        cut_size = word_len - i
        lemma_suff = stem[i:]
        code = self._SHIFT * tag + cut_size
        return lemma_suff, code

    def encode(self, word: str, rep: tuple) -> tuple:
        tag_code = rep[1] // self._SHIFT
        cut_size = rep[1] % self._SHIFT
        add = rep[0]
        lemma = word[0:len(word)-cut_size] + add
        return lemma, tag_code
