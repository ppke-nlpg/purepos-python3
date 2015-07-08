#!/usr/bin/env Python3
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
from purepos.model.probmodel import BaseProbabilityModel, OneWordLexicalModel

# todo ANAL_SPLIT_RE = "\|\|"
ANAL_SPLIT_RE = "||"

def parse(token: str) -> tuple:
    # todo beégetett szepartor?
    word_rb = token.find("{{")
    anal_rb = token.find("}}")
    word = token[:word_rb]
    anals_strs = token[word_rb+2:anal_rb]  # todo beégetett szepartor? +2!
    anals_list = anals_strs.split(ANAL_SPLIT_RE)
    return word, anals_list


def ispreanalysed(word: str) -> bool:
    return word.find("{{") > 0 and word.rfind("}}") > 0  # todo beégetett szepartor?


def clean(word: str) -> str:
    return word[:word.find("{{")]  # todo beégetett szepartor?


def anal2tag(anal: str) -> str:
    return anal[anal.find("["):]  # todo beégetett szepartor?


def anal2lemma(anal: str) -> str:
    return anal[:anal.find("[")]  # todo beégetett szepartor?


class AnalysisQueue:
    def __init__(self):
        self.anals = []
        self.use_prob = []
        self.words = []

    def init(self, capacity: int):
        self.anals = [None for x in range(capacity)]
        self.use_prob = [None for x in range(capacity)]
        self.words = [None for x in range(capacity)]

    def add_word(self, input: str, position: int):
        r = parse(input())
        word = r[0]
        anals_list = r[1]

        self.words[position] = word
        self.anals[position] = {}

        for anal in anals_list:
            val_sep_index = anal.find("$$")  # todo beégetett szepartor?
            lemmatag = anal
            prob = 1.0
            if val_sep_index > -1:
                self.use_prob[position] = True
                prob = float(anal[val_sep_index+2:])
                lemmatag = anal[:val_sep_index]

    def has_anal(self, position: int) -> bool:
        return len(self.anals) > position and self.anals[position] is not None

    # def getAnals(self, position):
    # anals.[position]

    def use_probabilities(self, pos: int) -> bool:
        if len(self.use_prob) > pos:
            return self.use_prob[pos] is not None
        else:
            return False

    def lexical_model_for_word(self, pos: int, tag_voc: BaseVocabulary) -> BaseProbabilityModel:
        map = self.transform_tags(pos, tag_voc)
        return OneWordLexicalModel(map, self.words[pos])

    def transform_tags(self, pos: int, tag_voc: BaseVocabulary) -> dict:
        map = {}
        for k, v in self.anals[pos]:
            tagstr = anal2tag(k)
            tag = tag_voc.index(tagstr)
            if tag is None:
                tag = tag_voc.add_element(tagstr)
            map[tag] = v
        return map

    def tags(self, pos: int, tag_voc: BaseVocabulary) -> set:
        return set(self.transform_tags(pos, tag_voc).keys())

    def analysises(self, pos: int) -> set:
        fanals = self.anals[pos].keys()
        ret = set()
        for fa in fanals:
            ret.add(Token(self.words[pos], anal2lemma(fa), anal2tag(fa)))
        return ret


