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
from purepos.common import util


class LemmaUnigramModel:
    def __init__(self):
        self.counter_map = dict()

    def increment(self, element):
        if element not in self.counter_map.keys():
            self.counter_map[element] = 1
        else:
            self.counter_map[element] += 1

    def count(self, element) -> int:
        return self.counter_map.get(element, 0)

    def __len__(self):
        return len(self.counter_map)

    def prob(self, s) -> float:
        return self.count(s) / len(self.counter_map)

    def log_prob(self, s):
        prob = self.prob(s)
        return math.log(prob) if prob > 0 else util.UNKOWN_VALUE
