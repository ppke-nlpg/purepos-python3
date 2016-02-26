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

from math import log
from purepos.configuration import Configuration
from purepos.common.corpusrepresentation import Token
from purepos.model.vocabulary import IntVocabulary


class UserProbSumNotOneError(Exception):
    pass


class OneWordLexicalModel:  # AnalysisQueue by element...
    def __init__(self, probs: dict, word: str, anals: set, use_probs):
        self.element_mapper = None
        self.context_mapper = None
        self.probs = probs
        self.word = word
        self.anals = list(anals)
        self.use_probabilities = use_probs

    def log_prob(self, context: list, word: str, unk_value) -> float:
        if self.element_mapper is not None:
            word = self.element_mapper.map(word)
        if self.context_mapper is not None:
            context = self.context_mapper.map_list(context[-1])  # Is contextmapper and element mapper differs?
        tag = context[-1]
        if word == self.word and tag in self.probs.keys():
            return self.probs[tag]
        return unk_value

    def word_tags(self) -> list:
        return list(self.probs.keys())

    def word_anals(self) -> list:
        return [Token(self.word, anal, prob) for anal, prob in self.probs.items()]


class AnalysisQueue:  # The user can add his or her own anals optionally with probs (This is just a parser!)
    # todo ki kéne tesztelni ilyen szintaktikájú korpuszon!!!
    def ispreanalysed(self, word: str) -> bool:
        return word.find(self.ANAL_OPEN) > 0 and word.rfind(self.ANAL_CLOSE) > 0

    def clean(self, word: str) -> str:
        return word[:word.find(self.ANAL_OPEN)]

    def __init__(self, conf: Configuration, ANAL_SEP='||', ANAL_OPEN='{{', ANAL_CLOSE='}}', ANAL_TAG_OPEN='[',
                 ANAL_TAG_CLOSE=']', PROB_SEP='$$'):
        self.ANAL_SEP = ANAL_SEP
        self.ANAL_OPEN = ANAL_OPEN
        self.ANAL_CLOSE = ANAL_CLOSE
        self.ANAL_TAG_OPEN = ANAL_TAG_OPEN
        self.ANAL_TAG_CLOSE = ANAL_TAG_CLOSE
        self.PROB_SEP = PROB_SEP
        self.conf = conf

    def parse(self, token: str, tag_voc: IntVocabulary):
        word_rb = token.find(self.ANAL_OPEN)
        anal_rb = token.find(self.ANAL_CLOSE)
        word = token[:word_rb]
        anals_strs = token[word_rb + len(self.ANAL_OPEN):anal_rb]
        anals_list = anals_strs.split(self.ANAL_SEP)

        tags = {}
        anals = set()
        sum_probs = 0.0
        use_prob = False
        for anal in anals_list:
            prob = 0.0  # LOGPROB! == 1.0 in normal prob...
            val_sep_index = anal.find(self.PROB_SEP)  # Separate prob if exists
            if val_sep_index > -1:
                use_prob = True
                prob = float(anal[val_sep_index + len(self.PROB_SEP):])
                sum_probs += prob
                if prob > 0.0:
                    prob = log(prob)
                else:
                    prob = self.conf.UNKNOWN_VALUE
                anal = anal[:val_sep_index]
            tag_rb = anal.find(self.ANAL_TAG_OPEN)  # Separate lemma from tag if exists
            tag_lb = anal.find(self.ANAL_TAG_CLOSE)
            lemma = anal[:tag_rb]
            tag = tag_voc.add_element(anal[tag_rb + len(self.ANAL_TAG_OPEN):tag_lb])  # Tag transformed to ID...
            tags[tag] = prob
            anals.add(Token(word, lemma, tag))
        if 0.0 < sum_probs < 1.0:
            raise UserProbSumNotOneError('The sum of probs is ({}) not 1.0 at token: \'{}\' !'.format(sum_probs, token))
        return OneWordLexicalModel(tags, word, anals, use_prob)
