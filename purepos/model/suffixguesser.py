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
from collections import Counter
from math import sqrt

__author__ = 'morta@digitus.itk.ppke.hu'

import math
from purepos.common.util import UNKNOWN_VALUE


class HashSuffixGuesser:  # (BaseSuffixGuesser):
    def __init__(self, freq_table: dict, theta: float):
        self.freq_table = freq_table
        self.theta = theta
        self.theta_plus_one = theta + 1
        self.mapper = None
        self.lemma_mapper = None

    def tag_log_probabilities(self, word) -> dict:
        mret = dict()
        freq_table = self.freq_table
        theta = self.theta
        theta_plus_one = self.theta_plus_one
        # Bug in PurePOS: If a word case differs from its lemmas cas (start of a sentence)
        # it won't be included in the freq_table! (Not yet fixed!)
        for i in range(len(word), -1, -1):
            # Brants (2000) formula 7
            suffix, prob = freq_table.get(word[i:], [dict(), 0])
            mret.update({tag: (mret.get(tag, 0.0) + (val / prob * theta)) / theta_plus_one
                         for tag, val in suffix.items()})
        return {k: math.log(v) for k, v in mret.items()}

    def tag_log_probability(self, word, tag) -> float:
        if self.mapper is not None:
            tag = self.mapper.map(tag)
        return self.tag_log_probabilities(word).get(tag, UNKNOWN_VALUE)

    def __str__(self):
        return str(self.freq_table)

    """
    # todo not used?
    def tag_prob_hunpos(self, word, tag) -> float:
        ret = 0.0
        for i in range(len(word)-1, -1, -1):
            suffix_value = self.freq_table.get(word[:i])
            if suffix_value is not None:
                tag_suff_freq = suffix_value[0].get(tag)
                if tag_suff_freq is not None:
                    ret = (ret + (tag_suff_freq / suffix_value[1] * self.theta))\
                        / self.theta_plus_one
                else:
                    break
        return ret
    """


class HashSuffixTree:

    @staticmethod
    def calculate_theta(apriori_probs: dict):
        """
        The original solution of brants have been replaced in HunPOS by following libmoot where multiple
        version of theta calculation is available see mooSuffixTrie.cc.
        We blindly follow them.
        :param apriori_probs: apriori tag probs
        :return: theta
        """
        # Simmilar to Brants (2000) formula 11 (see docstring above)
        pav = sum(val**2 for val in apriori_probs.values())
        # Simmilar to Brants (2000) formula 10 (see docstring above)
        theta = sqrt(sum(a_prob * ((a_prob-pav)**2) for a_prob in apriori_probs.values()))
        return theta

    def __init__(self, max_suff_len: int):
        self.max_suffix_length = max_suff_len
        self.total_tag_count = 0
        self.representation = dict()

    def add_word(self, word, tag, count: int, min_len: int=0):
        """
        Count all suffix of a word from a given position till the end of the word
        :param word: word
        :param tag:  tag
        :param count: count of observations
        :param min_len: minimal suffix length
        :return: None
        """
        end = len(word) - min_len
        start = max(0, end-self.max_suffix_length)
        for p in range(start, end + 1):
            suffix = word[p:]
            tags_counts = self.representation.setdefault(suffix, [Counter(), 0])[0]
            tags_counts[tag] += count
            self.representation[suffix][1] += count
        self.total_tag_count += count

    def create_guesser(self, theta: float) -> HashSuffixGuesser:
        return HashSuffixGuesser(self.representation, theta)


# XXX REPLACE to suffixguesser.py
# class HashLemmaTree(HashSuffixTree):
#     def __init__(self, max_suffix_length: int=10):
#         super().__init__(max_suffix_length)
