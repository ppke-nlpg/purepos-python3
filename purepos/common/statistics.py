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

from purepos.model.model import BaseModel


class Statistics:
    def __init__(self):
        self.sentences = 0
        self.tokens = 0
        self.l_guesser_items = 0
        self.u_guesser_items = 0
        self.theta = None  # todo float. Használjuk egyáltalán?

    def increment_lower_guesser_items(self, num: int):
        self.l_guesser_items += num

    def increment_upper_guesser_items(self, num: int):
        self.u_guesser_items += num

    def increment_token_count(self):
        self.tokens += 1

    def increment_sentence_count(self):
        self.sentences += 1

    def stat(self, model: BaseModel):
        return \
            """Training corpus:
{} tokens
{} sentences
{} different tag

Guesser trained with
{} lowercase
{} uppercase tokens
theta {}""".format(self.tokens,
                   self.sentences,
                   len(model.data.tag_vocabulary),
                   self.l_guesser_items,
                   self.u_guesser_items,
                   self.theta)

    def __eq__(self, other):
        return isinstance(other, Statistics) and \
            self.sentences == other.sentences and \
            self.tokens == other.tokens and \
            self.l_guesser_items == other.l_guesser_items and \
            self.u_guesser_items == other.u_guesser_items and \
            self.theta == other.theta
