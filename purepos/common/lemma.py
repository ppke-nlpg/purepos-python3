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

import re
from purepos.model.vocabulary import BaseVocabulary


main_pos_pat = re.compile("\[([^.\]]*)[.\]]")  # todo: ez csak át lett másolva. \? Jól működik!


# ok.
def batch_convert(prob_map: dict, word: str, vocab: BaseVocabulary) -> dict:
    ret = dict()
    for k, v in prob_map.items():
        lemma = k.convert(word, vocab)
        ret[lemma] = (k, v)
    return ret


def main_pos_tag(tag: str):
    m = re.match(main_pos_pat, tag)
    if m is not None:
        return m.group(1)
    else:
        return None
