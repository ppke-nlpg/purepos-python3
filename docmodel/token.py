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

SEP = "#"  # todo: változtatható legyen!

class Token:
    """Class representing a stemmed tagged token in a sentence."""

    def __init__(self, token: str, tag: str=None, stem: str=None):
        self.token = token
        self.tag = tag
        self.stem = stem

    def __str__(self):
        if self.token is None and self.stem is None:
            return None # todo: esetleg inkább ""
        if self.tag is not None and self.stem is None:
            return self.token + SEP + self.tag
        else:
            return self.token + SEP + self.stem + SEP + self.tag

    def __eq__(self, other):
        if other is not None and isinstance(other, Token):
            return (other.token == self.token) and\
                   (other.stem == self.stem) and \
                   (other.tag == self.tag)
        else:
            return False


class ModToken(Token):
    def __init__(self, token: str, tag: str=None, stem: str=None, original_stem: str=None):
        self.original_stem = original_stem
        super().__init__(token, tag, stem)