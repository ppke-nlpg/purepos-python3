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

from purepos.model.probmodel import BaseProbabilityModel
from purepos.model.suffixguesser import BaseSuffixGuesser
from purepos.model.lemmaunigrammodel import LemmaUnigramModel
from purepos.model.mapper import TagMapper
from purepos.model.vocabulary import BaseVocabulary


class CompiledModelData:
    def __init__(self):
        self.unigram_lemma_model = LemmaUnigramModel()
        self.lemma_guesser = BaseSuffixGuesser()
        self.suffix_lemma_model = BaseSuffixGuesser()
        from purepos.model.combiner import BaseCombiner  # todo jó ez?
        self.combiner = BaseCombiner()
        self.tag_transition_model = BaseProbabilityModel()
        self.standard_emission_model = BaseProbabilityModel()
        self.spec_tokens_emission_model = BaseProbabilityModel()
        self.lower_case_suffix_guesser = BaseSuffixGuesser()
        self.upper_case_suffix_guesser = BaseSuffixGuesser()
        self.apriori_tag_probs = dict()

    # ez a utilból került ide.
    def add_mappings(self,
                     tag_vocabulary: BaseVocabulary,
                     tag_mappings: list):
        mapper = TagMapper(tag_vocabulary, tag_mappings)
        self.standard_emission_model.context_mapper = mapper
        self.spec_tokens_emission_model.context_mapper = mapper
        self.tag_transition_model.context_mapper = mapper
        self.tag_transition_model.element_mapper = mapper
        self.lower_case_suffix_guesser.tag_mapper = mapper
        self.upper_case_suffix_guesser.tag_mapper = mapper
