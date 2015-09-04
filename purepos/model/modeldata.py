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

from purepos.model.vocabulary import BaseVocabulary, IntVocabulary, Lexicon


class ModelData:
    # todo paraméterezhető legyen MAJD!
    EOS_TAG = "</S>"
    BOS_TAG = "<S>"
    BOS_TOKEN = "<SB>"
    EOS_TOKEN = "<SE>"

    def __init__(self, tagging_order: int,
                 emission_order: int,
                 suffix_length: int,
                 rare_frequency: int,
                 standard_tokens_lexicon: Lexicon,
                 spec_tokens_lexicon: Lexicon,
                 tag_vocabulary: BaseVocabulary):
        self.tagging_order = tagging_order
        self.emission_order = emission_order
        self.suffix_length = suffix_length
        self.rare_frequency = rare_frequency
        self.standard_tokens_lexicon = standard_tokens_lexicon
        self.spec_tokens_lexicon = spec_tokens_lexicon
        self.tag_vocabulary = tag_vocabulary
        self.eos_index = tag_vocabulary.add_element(ModelData.EOS_TAG)
        self.bos_index = tag_vocabulary.add_element(ModelData.BOS_TAG)

    @staticmethod
    def create(tagging_order: int,
               emission_order: int,
               suffix_length: int,
               rare_frequency: int):
        return ModelData(tagging_order, emission_order, suffix_length, rare_frequency,
                         Lexicon(), Lexicon(), IntVocabulary())
