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

import argparse
import os
import sys
import math
import importlib.machinery
from corpusreader.corpus_reader import CorpusReader
from corpusreader.tokenreaders import StemmedTaggedTokenReader
from docmodel.token import Token, Colors
from purepos.trainer import Trainer
from purepos.common.serializer import StandardSerializer
from purepos.common import util
from purepos.tagger import BaseTagger, POSTagger, MorphTagger
from purepos.morphology import NullAnalyser, MorphologicalTable, HumorAnalyser
from purepos.cli.configuration import Configuration
from purepos.common.analysisqueue import AnalysisQueue


def parse_arguments():
    parser = argparse.ArgumentParser("purepos", description="PurePos is an open source hybrid "
                                                            "morphological tagger.")
    # parser.add_argument("-h", "--help", help="Print this message.")
    parser.add_argument("command", help="Mode selection: train for training the "
                                        "tagger, tag for tagging a text with the given model.",
                        metavar="tag|train", type=str, choices=["tag", "train"])
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
                        metavar="<analyzer>", type=str, default="integrated", dest="morphology")
    parser.add_argument("-H", "--pyhumor-path",
                        help="Set the path of the PyHumor module where the Humor class is defined.",
                        metavar="<path>", type=str, default="")  # todo default path
    parser.add_argument("-L", "--lex-path",
                        help="Set the path of the lex file used by the Humor analyser.",
                        metavar="<path>", type=str, default="lex/")  # todo default path
    parser.add_argument("--only-pos-tags",
                        help="Do not perform stemming, output only POS tags. Tagging only option.",
                        action="store_true", dest="no_stemming")
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
    parser.add_argument("--color-stdout",
                        help="Use colored console if the stdout is the choosen output.",
                        action="store_true")
    parser.add_argument("-c", "--encoding",
                        help="Encoding used to read the training set, or write the results. "
                             "The default is your OS default.",
                        metavar="<encoding>", type=str, default=sys.getdefaultencoding())
    parser.add_argument("--input-separator",
                        help="Separator characters and tag starting character for annotated input "
                             "(divided by the first character cf. sed). Eg.: \"#{{#||#}}#[\"",
                        metavar="<separators>", type=str, default=" {{ || }} [")
    parser.add_argument("-S", "--separator",
                        help="Separator character between word, lemma and tags. Default: '#'",
                        metavar="<separator>", type=str, default="#")
    parser.add_argument("-i", "--input-file",
                        help="File containg the training set (for tagging) or the text to be tagged"
                             " (for tagging). The default is the standard input.",
                        metavar="<file>", type=str, default=None)
    parser.add_argument("-d", "--beam-decoder",
                        help="Use Beam Search decoder. The default is to employ the Viterbi "
                             "algorithm. Tagging only option.", action="store_true")
    # todo beam_size
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
    def train(encoding: str,
              model_path: str,
              input_path: str or None,
              tag_order: int,
              emission_order: int,
              suff_length: int,
              rare_freq: int,
              separator: str,
              linesep: str):
        if input_path is not None:
            source = open(input_path, encoding=encoding)  # todo default encoding? (a Python3 okos)
        else:
            source = sys.stdin
        trainer = Trainer(source, CorpusReader(StemmedTaggedTokenReader(separator, linesep)))
        if os.path.isfile(model_path):
            print("Reading model... ", file=sys.stderr)
            ret_model = StandardSerializer.read_model(model_path)
            print("Training model... ", file=sys.stderr)
            ret_model = trainer.train_model(ret_model)
        else:
            print("Training model... ", file=sys.stderr)
            ret_model = trainer.train(tag_order, emission_order, suff_length, rare_freq)
        print(trainer.stat.stat(ret_model), file=sys.stderr)
        print("Writing model... ", file=sys.stderr)
        StandardSerializer.write_model(ret_model, model_path)
        print("Done!", file=sys.stderr)

    @staticmethod
    def tag(encoding: str,
            model_path: str,
            input_path: str,
            analyser: str,
            no_stemming: bool,
            max_guessed: int,
            max_resnum: int,
            beam_theta: int,
            use_beam_search: bool,
            out_path: str,
            use_colored_stdout: bool,
            humor_path: str,
            lex_path: str):  # todo IDÁIG KIHOZNI A HUMOR KONSTRUKTOR ELEMEIT *args, **kwargs
        if not input_path:
            source = sys.stdin
            if use_colored_stdout:
                # HEADER = '\033[95m'
                # OKBLUE = '\033[94m'
                # OKGREEN = '\033[92m'
                # WARNING = '\033[93m'
                # FAIL = '\033[91m'
                # ENDC = '\033[0m'
                # BOLD = '\033[1m'
                # UNDERLINE = '\033[4m'  # todo legyen témázható.
                Colors.ENDC = '\033[0m'
                Colors.WORD = '\033[97m'
                Colors.LEMMA = '\033[91m'
                Colors.TAGS = '\033[36m'
                Colors.SEPARATOR = '\033[90m'
        else:
            source = open(input_path, encoding=encoding)  # todo default encoding? (a Python3 okos)

        tagger = PurePos.create_tagger(model_path, analyser, no_stemming, max_guessed,
                                       math.log(beam_theta), use_beam_search, util.CONFIGURATION,
                                       humor_path, lex_path)
        if not out_path:
            output = sys.stdout
        else:
            output = open(out_path, mode="w", encoding=encoding)
        print("Tagging:", file=sys.stderr)
        tagger.tag(source, output, max_resnum)

    @staticmethod
    def load_humor(humor_path: str, lex_path: str) -> HumorAnalyser:
        humor_module = importlib.machinery.SourceFileLoader("humor", humor_path).load_module()
        humor = humor_module.Humor(_lex_path=lex_path)
        return HumorAnalyser(humor)

    @staticmethod
    def create_tagger(model_path: str,
                      analyser: str,
                      no_stemming: bool,
                      max_guessed: int,
                      beam_log_theta: float,
                      use_beam_search: bool,
                      conf: Configuration,
                      humor_path: str,
                      lex_path: str) -> BaseTagger:
        if analyser == PurePos.INTEGRATED_MA:
            try:
                ma = PurePos.load_humor(humor_path, lex_path)
            except FileNotFoundError:
                print("Humor module not found. Not using any morphological analyzer.",
                      file=sys.stderr)
                ma = NullAnalyser()
        elif analyser == PurePos.NONE_MA:
            ma = NullAnalyser()
        else:
            print("Using morphological table at: {}.".format(analyser), file=sys.stderr)
            ma = MorphologicalTable(open(analyser))
        print("Reading model... ", file=sys.stderr)
        rawmodel = StandardSerializer.read_model(model_path)
        print("Compiling model... ", file=sys.stderr)
        cmodel = rawmodel.compile(conf)
        suff_log_theta = math.log(10)
        if no_stemming:
            tagger = POSTagger(cmodel, ma, beam_log_theta,
                               suff_log_theta, max_guessed, use_beam_search)
        else:
            tagger = MorphTagger(cmodel, ma, beam_log_theta, suff_log_theta,
                                 max_guessed, use_beam_search)
        return tagger

    def __init__(self, options: dict):
        self.options = options
        seps = options["input_separator"][1:].split(options["input_separator"][0])
        AnalysisQueue.ANAL_OPEN = seps[0]
        AnalysisQueue.ANAL_SPLIT_RE = seps[1]
        AnalysisQueue.ANAL_CLOSE = seps[2]
        AnalysisQueue.ANAL_TAG_OPEN = seps[3]

    def run(self):
        if self.options.get("config_file") is None:
            util.CONFIGURATION = Configuration()
        else:
            util.CONFIGURATION = Configuration.read(self.options["config_file"])
        Token.SEP = self.options["separator"]
        if self.options["command"] == self.TRAIN_OPT:
            self.train(self.options["encoding"],
                       self.options["model"],
                       self.options["input_file"],
                       self.options["tag_order"],
                       self.options["emission_order"],
                       self.options["suffix_length"],
                       self.options["rare_frequency"],
                       self.options["separator"],
                       "\n")  # todo sor elválasztó?
        elif self.options["command"] == self.TAG_OPT:
            self.tag(self.options["encoding"],
                     self.options["model"],
                     self.options["input_file"],
                     self.options["morphology"],
                     self.options.get("no_stemming", False),
                     self.options["max_guessed"],
                     self.options["max_results"],
                     self.options["beam_theta"],
                     self.options.get("beam_decoder", False),
                     self.options["output_file"],
                     self.options.get("color_stdout", False),
                     self.options["pyhumor_path"],
                     self.options["lex_path"])


def main():
    options = parse_arguments()
    PurePos(vars(options)).run()

if __name__ == '__main__':
    main()
