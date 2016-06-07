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

from collections import Counter
from math import sqrt, log


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

    def __str__(self):
        return str(self.freq_table)

    def __init__(self, max_suff_len: int):
        self.max_suffix_length = max_suff_len
        self.total_tag_count = 0
        self.freq_table = dict()
        self.theta = None
        self.mapper = None

    def add_word(self, word, tag, count: int, min_len: int=0):
        """
        Count all suffix of a word from a given position till the end of the word
        :param word: word
        :param tag:  tag
        :param count: count of observations
        :param min_len: minimal suffix length
        :return: None
        """
        wlen = len(word)
        # Here we can add anything...
        for suffix in (word[wlen-i:] for i in range(min_len, min(wlen, self.max_suffix_length)+1)):
            tags_counts = self.freq_table.setdefault(suffix, [Counter(), 0])[0]  # Return or return default...
            tags_counts[tag] += count            # Increment (suffix, tag) count
            self.freq_table[suffix][1] += count  # Increment suffix count
        self.total_tag_count += count            # Increment tag count for all tags

    def create_guesser(self, theta: float):
        self.theta = theta

    def tag_log_probabilities(self, word) -> dict:
        mret = dict()
        freq_table = self.freq_table
        theta = self.theta
        theta_plus_one = theta + 1
        wlen = len(word)
        # Bug in PurePOS: If a word case differs from its lemmas case (start of a sentence)
        # it won't be included in the freq_table! (Fixed!)
        # Here we do not want to accept lemmas, with - at the end...
        # todo: Ez most mit csinál ha -- a szó?
        # todo: Ez most kezeli a batch_convert-ben a többértelműséget? (Elvileg kéne neki.)
        for suffix in (word[wlen-i:] for i in range(min(wlen, self.max_suffix_length)+1)
                       if not word[:wlen-i].endswith('-')):
            # Brants (2000) formula 7
            suffix, suffix_count = freq_table.get(suffix, [dict(), 0])
            for tag, tcount in suffix.items():
                mret[tag] = (mret.get(tag, 0.0) + (tcount / suffix_count * theta)) / theta_plus_one
        return {k: log(v) for k, v in mret.items()}

    def tag_log_probability(self, word, tag, unk_value) -> float:
        if self.mapper is not None:
            tag = self.mapper.map(tag)
        return self.tag_log_probabilities(word).get(tag, unk_value)

    def tag_log_probabilities_w_max(self, word, max_guessed_tags: int, suf_theta: float) -> dict:
        # Prune guessed tags: Filter most probable tags to avoid them for OOVS (Brants 2000, sect 2.3, 4. point)
        guessed_tags = self.tag_log_probabilities(word)
        min_val = max(guessed_tags.values()) - suf_theta  # Max probability - theta
        pruned_guessed_tags = {(k, v) for k, v in guessed_tags.items() if v > min_val}
        if len(pruned_guessed_tags) > max_guessed_tags:
            pruned_guessed_tags = sorted(pruned_guessed_tags, key=lambda ent: ent[1],
                                         reverse=True)[-max_guessed_tags:]
        return pruned_guessed_tags
