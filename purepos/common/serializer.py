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

from io import IOBase
import pickle
import os
from purepos.model.model import RawModel


class StandardSerializer:
    # todo esetleg file helyett filename?
    @staticmethod
    def read_model(file: IOBase) -> RawModel:
        return pickle.load(file)

    @staticmethod
    def write_model(model: RawModel, file: IOBase):
        pickle.dump(model, file)

    @staticmethod
    def delete_model(filename: str):
        try:
            os.remove(filename)
        except FileNotFoundError:
            raise Warning("Invalid filename! Nothing deleted.")
