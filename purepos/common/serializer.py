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

import pickle
import os
from purepos.model.rawmodel import RawModel


class StandardSerializer:
    @staticmethod
    def read_model(filename: str) -> RawModel:
        with open(filename, mode="rb") as file:
            return pickle.load(file)

    @staticmethod
    def write_model(model: RawModel, filename: str):
        with open(filename, mode="wb") as file:
            pickle.dump(model, file)

    @staticmethod
    def delete_model(filename: str):
        try:
            os.remove(filename)
        except FileNotFoundError:
            raise Warning("Invalid filename! Nothing deleted.")
