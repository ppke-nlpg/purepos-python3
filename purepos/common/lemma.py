#!/usr/bin/env Python3
# todo nincs kész
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

import re
from docmodel.token import Token
from purepos.model.combiner import BaseCombiner, LogLinearBiCombiner
from purepos.model.vocabulary import BaseVocabulary
from purepos.model.modeldata import ModelData, RawModelData, CompiledModelData


main_pos_pat = re.compile("\\[([^.\\]]*)[.\\]]")  # todo: ez csak át lett másolva. \? Jól működik!


def batch_convert(prob_map: dict, word: str, vocab: BaseVocabulary):
    ret = {}
    for k, v in prob_map:
        lemma = k.convert(word, vocab)
        ret[lemma] = (k, v)
    return ret


def def_lemma_representation(word, stem, tag):
    return SuffixLemmaTransformation(word, stem, tag)


def def_lemma_representation_by_token(token: Token, data: ModelData):  # todo inline!
    return def_lemma_representation(token.token, token.stem, data.tag_vocabulary.index(token.tag))


def default_combiner():
    return LogLinearBiCombiner()


def store_lemma(
        word: str,
        lemma: str,
        tag: int,
        tagstring: str,
        raw_modeldata: RawModelData):
    raw_modeldata.lemma_unigram_model.increment(lemma)
    cnt = 1
    lemmatrans = def_lemma_representation(word, lemma, tag)
    raw_modeldata.lemma_suffix_tree.add_word(word, lemmatrans, cnt, lemmatrans.min_cut_length())
    # todo ilyen nem létezik.


def main_pos_tag(tag: str):
    m = re.match(main_pos_pat, tag)
    if m is not None:
        return m.group(1)
    else:
        return None


def longest_substring(str1: str, str2: str) -> tuple:
    """
    Calculates the longest substring efficiently.
    :param str1:
    :param str2:
    :return: start position and length
    """
    if not str1 or not str2:
        return 0, 0
    sb = []
    str1 = str1.lower()
    str2 = str2.lower()
    num = [[0 for x in range(len(str1))] for x in range(str2)]
    maxlen = 0
    last_begin = 0

    for i, s1 in enumerate(str1):
        for j, s2 in enumerate(str2):
            if s1 == s2:
                if i == 0 or j == 0:
                    num[i][j] = 1
                else:
                    num[i][j] = 1 + num[i - 1][j - 1]

                if num[i][j] > maxlen:
                    maxlen = num[i][j]
                    this_begin = i - num[i][j] + 1
                    if last_begin == this_begin:
                        sb.append(s1)
                    else:
                        last_begin = this_begin
                        sb.clear()
                        sb.append(str1[last_begin:i+1])
    return last_begin, len(str.join('', sb))


def lower_transformed(word: str, lemma: str) -> bool:
    if len(word) > 0 and len(lemma) > 0:
        return word[0].isupper() and lemma[0].islower()
    return False


class LemmaComparator:
    def __init__(self, compilde_model_data: CompiledModelData, model_data: ModelData):
        self.comp_model_data = compilde_model_data
        self.model_data = model_data

    def compare(self, t1: tuple, t2: tuple):
        # todo Java comparable interfész. Hol használjuk? Mire kell átírni?
        combiner = self.comp_model_data.combiner
        final_score1 = combiner.combine(t1[0], t1[1], self.comp_model_data, self.model_data)
        final_score2 = combiner.combine(t2[0], t2[1], self.comp_model_data, self.model_data)
        if final_score1 == final_score2:
            return 0
        if final_score1 < final_score2:
            return -1
        else:
            return 1


class BaseLemmaTransformation:
    def __init__(self, word: str, lemma: str, tag: int):
        self.representation = self.decode(word, lemma, tag)

    def analyse(self, word) -> tuple:
        encoded = self.encode(word, self.representation)
        return self.postprocess(encoded[0]), encoded[1]

    def min_cut_length(self) -> int:
        pass

    def convert(self, word: str, vocab: BaseVocabulary) -> Token:
        anal = self.analyse(word)
        tag = vocab.word(anal[1])
        return Token(word, anal[0], tag)

    # def __str__(self) -> str:
    #     return self.representation.__str__()
    # todo unkomment, ha kell.

    def __eq__(self, other) -> bool:
        return isinstance(other, type(self)) and self.representation == other.representation
        # todd: leszármazottakkal újra áttekinteni

    def decode(self, word: str, lemma: str, tag: int):
        ...

    def encode(self, word: str, rep) -> tuple:
        ...

    def postprocess(self, lemma: str) -> str:
        if len(lemma) > 1 and lemma[-1] == '-':
            return lemma[:-1]
        return lemma
        # todo ehelyett esetleg return lemma.rstrip('-')

    def token(self, word: str, lemma: str, tag: int) -> Token:
        return Token(word, lemma, tag)


class GeneralizedLemmaTransformation(BaseLemmaTransformation):
    class Transformation:
        def __init__(self, remove_start: int, remove_end: int, add_start: str, add_end: str,
                     tag: int, to_lower: bool):
            self.remove_start = remove_start
            self.remove_end = remove_end
            self.add_start = add_start
            self.add_end = add_end
            self.tag = tag
            self.to_lower = to_lower
            l = "_" if self.to_lower else "-"
            self.str_rep = "(" + l + ",< -" + str(remove_start) + "+'" + add_start + "', " +\
                           ">-" + str(remove_end) + "+'" + add_end + "' -" + str(tag) + ")"

        def __str__(self):
            return self.str_rep

        def __eq__(self, other):
            return isinstance(other, GeneralizedLemmaTransformation.Transformation) and \
                self.remove_start == other.remove_start and \
                self.remove_end == other.remove_end and \
                self.add_start == other.add_start and \
                self.add_end == other.add_end and \
                self.tag == other.tag


    def __init__(self, word: str, lemma: str, tag: int):
        super().__init__(word, lemma, tag)

    def min_cut_length(self) -> int:
        return self.representation.remove_end

    def decode(self, word: str, lemma: str, tag: int) -> Transformation:
        pos_word_lemma = longest_substring(word, lemma)
        pos_lemma_word = longest_substring(lemma, word)
        lowered = lower_transformed(word, lemma)
        if pos_word_lemma[1] < 2:
            return GeneralizedLemmaTransformation.Transformation(
                0, len(word), "", lemma, tag, lowered)
        remove_start = pos_word_lemma[0]
        remove_end = len(word) - (pos_word_lemma[0] + pos_word_lemma[1])
        add_start = lemma[0:pos_lemma_word[0]]
        add_end = lemma[pos_lemma_word[0] + pos_lemma_word[1]]
        return GeneralizedLemmaTransformation.Transformation(remove_start, remove_end, add_start,
                                                             add_end, tag, lowered)

    def encode(self, word: str, rep: Transformation) -> tuple:
        upper_word = not (word == word.lower())
        sub_end = max(0, len(word) - rep.remove_end)
        lemma = word[0:sub_end] + rep.add_end
        lemma = (rep.add_start + lemma[min(rep.remove_start, len(lemma)):]).lower()
        if upper_word and not rep.to_lower and len(lemma) > 0:
            lemma = lemma[0].upper()+lemma[1:]
        return lemma, rep.tag


class SuffixLemmaTransformation(BaseLemmaTransformation):
    SHIFT = 100

    def __init__(self, word: str, lemma: str, tag: int):
        super().__init__(word, lemma, tag)

    def decode(self, word: str, stem: str, tag: int) -> tuple:
        i = 0
        for idx in range(min(len(word), len(stem))):
            i = idx
            if word[idx] != stem[idx]:
                break
        word_suff = word[i:]
        cut_size = len(word_suff)
        lemma_suff = stem[i:]
        code = SuffixLemmaTransformation.SHIFT * tag + cut_size
        return lemma_suff, code

    def encode(self, word: str, rep: tuple):
        tag_code = rep[1] / SuffixLemmaTransformation.SHIFT
        cut_size = rep[1] % SuffixLemmaTransformation.SHIFT
        add = rep[0]
        lemma = word[0:len(word)-cut_size]
        return lemma, tag_code

    def min_cut_length(self):
        return self.representation[1] % SuffixLemmaTransformation.SHIFT

