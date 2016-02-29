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

from purepos.common.lemmatransformation import LemmaTransformation
from purepos.common.corpusrepresentation import Token
from purepos.configuration import Configuration
from purepos.trainer import Model


def find_best_lemma(t: Token, position: int, analysis_queue, analyser, model, conf) -> Token:
    # todo: Ezt végig kéne gondolni, hogy tényleg így a legjobb-e...
    if analysis_queue[position] is not None:
        stems = analysis_queue[position].word_anals()
        for t in stems:
            t.simplify_lemma()
    else:
        stems = analyser.analyse(t.token)

    guessed = len(stems) == 0
    if guessed:
        # dict: lemma -> (lemmatrans, prob)
        lemma_suff_probs = {lemmatrans.encode(t.token, model.tag_vocabulary): (lemmatrans, prob)
                            for lemmatrans, prob in model.lemma_suffix_tree.tag_log_probabilities(t.token).items()}
        stems = lemma_suff_probs.keys()

    possible_stems = [ct for ct in stems if t.tag == ct.tag]

    if len(possible_stems) == 0:
        best = Token(t.token, t.token, t.tag)  # lemma = token
    elif len(possible_stems) == 1 and t.token == t.token.lower():  # If upper then it could be at sentence start...
        best = possible_stems[0]
    else:
        comp = []
        if not guessed:
            # dict: lemma -> (lemmatrans, prob)
            lemma_suff_probs = {lemmatrans.encode(t.token, model.tag_vocabulary): (lemmatrans, prob)
                                for lemmatrans, prob in model.lemma_suffix_tree.tag_log_probabilities(t.token).items()}
        for poss_tok in possible_stems:
            pair = lemma_suff_probs.get(poss_tok)  # (lemmatrans, prob)
            if pair is not None:
                traf = pair[0]
            else:
                traf = LemmaTransformation(poss_tok.token, poss_tok.stem,
                                           model.tag_vocabulary.index(poss_tok.tag))  # Get
            comp.append((poss_tok, traf))
            if guessed:  # Append lowercased stems...
                lower_tok = Token(poss_tok.token, poss_tok.stem.lower(), poss_tok.tag)
                comp.append((lower_tok, traf))
        best = (max(comp, key=lambda p: model.combiner.combine(p[0], p[1], model)))[0]

    if best.original_stem is not None:
        best.stem = best.original_stem

    lemma = best.stem.replace(' ', '_')
    if guessed and conf is not None:
        lemma = conf.guessed_lemma_marker + lemma

    return Token(best.token, lemma, best.tag)


class LogLinearBiCombiner:
    def __init__(self, conf: Configuration):
        self.conf = conf
        self.lambdas = [1.0, 1.0]

    def calculate_params(self, modeldata: Model):
        lambda_u = self.lambdas[0]
        lambda_s = self.lambdas[1]
        for i, (tok, count) in enumerate(modeldata.corpus_types_w_count.items()):
            if i % 1000 == 0:
                print(i)
            suffix_probs = {lemmatrans.encode(tok.token, modeldata.tag_vocabulary): (lemmatrans, prob)
                            for lemmatrans, prob in modeldata.lemma_suffix_tree.tag_log_probabilities(tok.token).items()}
            # Tokens mapped to unigram score and the maximal score is selected
            uni_max_prob = max(modeldata.lemma_unigram_model.log_prob(t.stem, self.conf.UNKNOWN_VALUE)
                               for t in suffix_probs.keys())
            # Same with sufixes
            suffix_max_prob = max(prob for _, prob in suffix_probs.values())
            act_uni_prob = modeldata.lemma_unigram_model.log_prob(tok.stem, self.conf.UNKNOWN_VALUE)
            # todo: Itt lehegy egyáltalán UNKNOWN? Nem mert ezt tanulja meg...
            act_suff_prob = suffix_probs.get(tok, (None, self.conf.UNKNOWN_VALUE))[1]

            uni_prop = act_uni_prob - uni_max_prob
            suff_prop = act_suff_prob - suffix_max_prob
            if uni_prop > suff_prop:
                lambda_u += (uni_prop - suff_prop) * count
            elif suff_prop > uni_prop:
                lambda_s += (suff_prop - uni_prop) * count

        s = lambda_u + lambda_s
        lambda_u /= s
        lambda_s /= s
        # Bug in PurePOS: incremental learning mishandle lambdas (only the first two elements used but others may added)
        self.lambdas[0] = lambda_u
        self.lambdas[1] = lambda_s

    def combine(self, token: Token, lem_transf: LemmaTransformation, modeldata: Model) -> float:
        if self.conf is not None and self.conf.weight is not None:
            self.lambdas[0] = self.conf.weight
            self.lambdas[1] = 1 - self.conf.weight

        return (self.lambdas[0] * modeldata.lemma_unigram_model.log_prob(token.stem, self.conf.UNKNOWN_VALUE) +
                self.lambdas[1] * modeldata.lemma_suffix_tree.tag_log_probability(token.token, lem_transf,
                                                                                  self.conf.UNKNOWN_VALUE))


# Csak a BiCombinert használjuk, ami innen jön, dead code.

"""
import re
main_pos_pat = re.compile("\[([^.\]]*)[.\]]")

def main_pos_tag(tag: str):
    m = re.match(main_pos_pat, tag)
    if m is not None:
        return m.group(1)

class LogLinearMLCombiner(BaseCombiner):
    def calculate_params(self, doc: Document,
                         raw_modeldata: RawModelData,
                         modeldata: ModelData):
        self.lambdas = [0.0, 0.1]

    def combine(self, token: Token, lem_transf: BaseLemmaTransformation, compiled_modeldata: CompiledModelData,
                modeldata: ModelData) -> float:
        return self.lambdas[0] * compiled_modeldata.unigram_lemma_model.log_prob(token.stem) + \
               self.lambdas[1] * compiled_modeldata.lemma_guesser.tag_log_probability(token.token, lem_transf)


class LogLinearTriCombiner(BaseCombiner):
    def calculate_params(self, doc: Document, raw_modeldata: RawModelData, modeldata: ModelData):
        theta = HashSuffixTree.calculate_theta(raw_modeldata.tag_ngram_model.count_word_apriori_probs())
        lemma_suffix_tag_log_probabilities = raw_modeldata.lemma_suffix_tree.create_guesser(theta).tag_log_probabilities
        lemma_unigram_model_log_prob = raw_modeldata.lemma_unigram_model.log_prob
        lemma_tag_log_probability = raw_modeldata.lemma_freq_tree.create_guesser(theta).tag_log_probability

        lambda_u, lambda_s, lambda_l = 1.0, 1.0, 1.0
        for sentence in doc.sentences():
            for tok in sentence:
                suffix_probs = batch_convert(lemma_suffix_tag_log_probabilities(tok.token), tok.token,
                                             modeldata.tag_vocabulary)
                uni_max_prob = max(lemma_unigram_model_log_prob(t.stem) for t in suffix_probs.keys())
                suffix_max_prob = max(prob for _, prob in suffix_probs.values())
                lemma_max_prob = max(lemma_tag_log_probability(t.stem, main_pos_tag(t.tag))
                                     for t in suffix_probs.keys())

                act_uni_prob = lemma_unigram_model_log_prob(tok.stem)
                act_suff_prob = suffix_probs.get(tok, (None, UNKNOWN_VALUE))[1]
                act_lemma_prob = lemma_tag_log_probability(tok.stem, main_pos_tag(tok.tag))

                uni_prop = act_uni_prob - uni_max_prob
                suff_prop = act_suff_prob - suffix_max_prob
                lemma_prop = act_lemma_prob - lemma_max_prob
                if uni_prop > suff_prop and uni_prop > lemma_prop:
                    lambda_u += uni_prop
                elif suff_prop > uni_prop and suff_prop > lemma_prop:
                    lambda_s += suff_prop
                elif lemma_prop > uni_prop and lemma_prop > suff_prop:
                    lambda_l += lemma_prop
        s = lambda_u + lambda_s + lambda_l
        lambda_u /= s
        lambda_s /= s
        lambda_l /= s
        self.lambdas.append(lambda_u)
        self.lambdas.append(lambda_s)
        self.lambdas.append(lambda_l)

    def combine(self, token: Token, lem_transf: BaseLemmaTransformation, compiled_modeldata: CompiledModelData,
                modeldata: ModelData) -> float:
        # uni_score + suffix_score + lemma_prob
        return self.lambdas[0] * compiled_modeldata.unigram_lemma_model.log_prob(token.stem) + \
               self.lambdas[1] * compiled_modeldata.lemma_guesser.tag_log_probability(token.token, lem_transf) + \
               self.lambdas[2] * compiled_modeldata.suffix_lemma_model.tag_log_probability(token.stem,
                                                                                           main_pos_tag(token.tag))
"""
