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

import math
UNKNOWN_VALUE = -99.0


class HashSuffixGuesser:  # (BaseSuffixGuesser):
    @staticmethod
    def max_probability_tag(probabilities: dict) -> int:
        m = max(probabilities.items(), key=lambda x: x[1])
        return m[0]

    def __init__(self, freq_table: dict, theta: float):
        self.freq_table = freq_table
        self.theta = theta
        self.theta_plus_one = theta + 1
        self.mapper = None
        self.lemma_mapper = None

    def tag_log_probabilities(self, word) -> dict:
        return {k: math.log(v) for k, v in self.tag_probabilities(word).items()}

    def tag_probabilities(self, word) -> dict:
        mret = dict()
        for i in range(len(word), -1, -1):
            suffix_value = self.freq_table.get(word[i:], [dict(), 0])
            mret.update({tag: (mret.get(tag, 0.0) + (float(val) / suffix_value[1] * self.theta))
                         / self.theta_plus_one
                         for tag, val in suffix_value[0].items()})
        return mret

    def tag_log_probability(self, word, tag) -> float:
        prob = self.tag_probability(word, tag)
        return math.log(prob) if prob > 0 else UNKNOWN_VALUE

    def tag_probability(self, word, tag) -> float:
        if self.mapper is not None:
            tag = self.mapper.map(tag)
        return self.tag_probabilities(word).get(tag, 0.0)

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

    def __str__(self):
        return str(self.freq_table)
