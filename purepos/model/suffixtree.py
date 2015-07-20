#!/usr/bin/env python3
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

from purepos.model.suffixguesser import BaseSuffixGuesser, HashSuffixGuesser
from purepos.common.lemma import BaseLemmaTransformation


class BaseSuffixTree:
    def __init__(self, max_suff_len: int):
        self.max_suffix_length = max_suff_len

    def add_word(self, word, tag, count: int, min_len: int=0):
        pass

    def create_guesser(self, theta: float) -> BaseSuffixGuesser:
        pass

    @staticmethod
    def calculate_theta(apriori_probs: dict):
        pav = 0.0
        for val in apriori_probs.values():
            pav += val**2
        theta = 0.0
        for a_prob in apriori_probs.values():
            theta += a_prob * ((a_prob-pav)**2)
        return theta**0.5


class HashSuffixTree(BaseSuffixTree):
    def __init__(self, max_suff_len: int):
        super().__init__(max_suff_len)
        self.total_tag_count = 0
        self.representation = dict()

    def add_word(self, word, tag, count: int, min_len: int=0):
        end = len(word) - min_len
        start = max(0, end-self.max_suffix_length)
        for p in range(start, end+1):
            suffix = word[p:]
            self.increment(suffix, tag, count)
        self.total_tag_count += count

    def increment(self, suffix: str, tag, cnt: int):
        if suffix in self.representation.keys():
            value = self.representation[suffix]
            tags_counts = value[0]
            if tag in tags_counts.keys():
                tags_counts[tag] += cnt
            else:
                tags_counts[tag] = cnt
            value[1] += cnt
        else:
            tags_counts = dict()
            tags_counts[tag] = cnt
            value = (tags_counts, cnt)
            self.representation[suffix] = value

    def create_guesser(self, theta: float) -> BaseSuffixGuesser:
        return HashSuffixGuesser(self.representation, theta)


class HashLemmaTree(HashSuffixTree):
    def __init__(self, max_suffix_length: int=10):
        super().__init__(max_suffix_length)

    def add_word(self, suff_str: str, tag: BaseLemmaTransformation, count: int, min_len: int=0):
        self.increment(suff_str, tag, count)
