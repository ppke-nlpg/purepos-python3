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

import argparse
import os
import sys


def parse_arguments():
    parser = argparse.ArgumentParser("PurePOS")
    # parser.add_argument("-h", "--help", help="Print this message.")
    parser.add_argument("command", help="Mode selection: train for training the tagger, tag for "
                                        "tagging a text with the given model.",
                        required=True, metavar="tag|train", type=str)  # todo esetleg default tag
    parser.add_argument("-m", "--model",
                        help="Specifies a path to a model file. If an exisiting model is given for "
                             "training, the tool performs incremental training.",
                        metavar="<modelfile>", required=True, type=str)
    parser.add_argument("-t", "--tag-order",
                        help="Order of tag transition. Second order means "
                             "trigram tagging. The default is 2. Training only option.",
                        metavar="<number>", type=int, default=2)
    parser.add_argument("-e", "--emission-order",
                        help="Order of emission. First order means that the given word depends "
                             "only on its tag. The default is 2.  Training only option.",
                        metavar="<number>", type=int, default=2)
    parser.add_argument("-s", "--suffix-length",
                        help="Use a suffix trie for guessing unknown words tags with the given "
                             "maximum suffix length. The default is 10.  Training only option.",
                        metavar="<length>", type=int, default=10)
    parser.add_argument("-r", "--rare-frequency",
                        help="Add only words to the suffix trie with frequency less than the given"
                             " treshold. The default is 10.  Training only option.",
                        metavar="<treshold>", type=int, default=10)
    parser.add_argument("-a", "--analyzer",
                        help="Set the morphological analyzer. <analyzer> can be "
                             "'none', 'integrated' or a file : <morphologicalTableFile>. The "
                             "default is to use the integrated one. Tagging only option. ",
                        metavar="<analyzer>", type=str, default="integrated") # todo lista, morph.
    # todo nosteming
    parser.add_argument("-g", "--max-guessed",
                        help="Limit the max guessed tags for each token. The default is 10. "
                             "Tagging only option.",
                        metavar="<number>", type=int, default=10)
    parser.add_argument("-n", "--max-results",
                        help="Set the expected maximum number of tag sequences (with its score). "
                             "The default is 1. Tagging only option.",
                        metavar="<number>", type=int, default=1)
    parser.add_argument("-b", "--beam-theta",
                        help="Set the beam-search limit. "
                             "The default is 1000. Tagging only option.",
                        metavar="<theta>", type=int, default=1000)
    parser.add_argument("-o", "--output-file",
                        help="File where the tagging output is redirected. Tagging only option.",
                        metavar="<file>", type=str, default=None)
    parser.add_argument("-c", "--encoding",
                        help="Encoding used to read the training set, or write the results. "
                             "The default is your OS default.",
                        metavar="<encoding>", type=str, default=sys.getdefaultencoding())
    parser.add_argument("-i", "--input-file",
                        help="File containg the training set (for tagging) or the text to be tagged"
                             " (for tagging). The default is the standard input.",
                        metavar="<file>", type=str, default=None)
    parser.add_argument("-d", "--beam-decoder",
                        help="Use Beam Search decoder. The default is to employ the Viterbi "
                             "algorithm. Tagging only option.", type=bool, default=False)  # todo
    #  a hatékonyabb legyen a defaut
    parser.add_argument("-f", "--config-file",
                        help="Configuratoin file containg tag mappings. "
                             "Defaults to do not map any tag.",
                        metavar="<file>", type=str, default=None)
    return parser.parse_args()


class PurePos:
    TAG_OPT = "tag"
    TRAIN_OPT = "train"
    PRE_MA = "pre"
    NONE_MA = "none"
    INTEGRATED_MA = "integrated"

    @staticmethod
    def train():
        pass

    @staticmethod
    def tag():
        pass

    @staticmethod
    def load_humor():
        pass

    def __init__(self, options: argparse.Namespace):
        self.options = options

    def run(self):
        pass


def main():
    options = parse_arguments()


if __name__ == '__main__':
    main()