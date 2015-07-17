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

import io
from corpusreader.corpus_reader import CorpusReader
from purepos.common.statistics import Statistics
from purepos.model.model import RawModel
from purepos.model.modeldata import ModelData

class Trainer:
    def __init__(self, source: io.TextIOWrapper, reader: CorpusReader):
        self.stat = Statistics()
        self.reader = reader
        self.document = reader.read_from_io(source)  # todo egybe beolvassa a memóriába.

    def train(self, tag_order: int,
              emission_order: int,
              max_suffix_length: int,
              rare_frequency: int) -> RawModel:
        return self.train_model(RawModel(ModelData.create(tag_order, emission_order,
                                                          max_suffix_length, rare_frequency)))

    def train_model(self, raw_model: RawModel) -> RawModel:
        raw_model.train(self.document)
        self.stat = raw_model.last_stat()
        return raw_model
