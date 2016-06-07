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

from purepos.common.morphology import Morphology
from purepos.common.spectokenmatcher import SpecTokenMatcher
from purepos.configuration import Configuration
from purepos.decoder.ngram import NGram, Node
from purepos.trainer import Model


class BeamedViterbi:
    def __init__(self, model: Model, morphological_analyzer: Morphology, log_theta: float,
                 suf_theta: float, max_guessed_tags: int, spectoken_matcher: SpecTokenMatcher, conf: Configuration,
                 beam_size: int=None):
        self.model = model
        self.tags = model.tag_vocabulary.tag_indices()
        self.morphological_analyzer = morphological_analyzer
        self.log_theta = log_theta
        self.suf_theta = suf_theta
        self.max_guessed_tags = max_guessed_tags
        self.spectoken_matcher_match_lexical_element = spectoken_matcher.match_lexical_element
        self.conf = conf
        self.beam_size = beam_size

    def next_probs(self, word: str, position: int, user_anals: list) -> tuple:
        # Computes the observation probabilities for the word. The acutal fuction is determied by the token's proerties!
        if word == self.conf.EOS_TOKEN:
            tags = [self.model.eos_index]
            seen = False
            # Dummy variables, not used...
            guesser = self.model.lower_suffix_tree
            lword = word
        else:
            # Defaults:
            # word_prob_model = spec_tokens_emission_model | spec_tokens_emission_model
            # tags = standard_token_lexicon | spec_tokens_lexicon
            word_form = word
            lword = word.lower()
            isupper = not (lword == word)
            word_prob_model = self.model.standard_emission_model
            tags = self.model.standard_tokens_lexicon.tags(word)
            morph_anals = [self.model.tag_vocabulary.add_element(tag) for tag in self.morphological_analyzer.tags(word)]
            seen = False

            if len(tags) > 0:
                # SEEN EXACTLY
                # word_prob_model = self.model.standard_emission_model
                # word_form = word
                seen = True
            else:  # elif
                tags = self.model.standard_tokens_lexicon.tags(lword)
                if position == 0 and isupper and len(tags) > 0:
                    # SEEN, BUT LOWERCASED: First of a sentence uppercase and seen only in lowercase form
                    # word_prob_model = self.model.standard_emission_model
                    word_form = lword
                    isupper = False
                    seen = True
                else:  # elif
                    # SPECIAL TOKEN?
                    spec_name = self.spectoken_matcher_match_lexical_element(word)
                    if spec_name is not None:
                        # Special, but was it seen?
                        word_prob_model = self.model.spec_tokens_emission_model
                        tags = self.model.spec_tokens_lexicon.tags(spec_name)
                        word_form = spec_name
                        if len(tags) > 0:
                            seen = True
                        else:
                            print('WARNING: \'{}\' is identified as special token ({}),'
                                  ' but not seen in the training set! Using Guesser...'.format(word, spec_name))

            # Set guesser for casing of word_form...
            if isupper:
                guesser = self.model.upper_suffix_tree
            else:
                guesser = self.model.lower_suffix_tree

            # User's own stuff... May overdefine (almost) everything... (left as is: isupper, lword, wordform)
            if user_anals[position] is not None:
                tags = user_anals[position].word_tags()
                if user_anals[position].use_probabilities:
                    word_prob_model = user_anals[position]  # If no probabilities, handle it like
                    seen = True                             # the morphological analyser (but without filtering)
            # User's morph_anals do not need filtering...
            # Filter tags with morphology (tags = tags & morph_anals )
            elif len(morph_anals) > 0 and seen:  # Because if not seen tags is empty
                if word_prob_model.context_mapper is not None:
                    common = set(word_prob_model.context_mapper.filter(morph_anals, tags))
                else:
                    common = set(morph_anals).intersection(tags)
                if len(common) > 0:
                    tags = common
            elif len(morph_anals) > 0:  # Use pure morphology, else no change in tags...
                tags = morph_anals

        tags = [(tag, 0.0) for tag in tags]  # todo: MAKE THIS EARLIER!
        UNK_TAG_TRANS = self.conf.UNK_TAG_TRANS
        if seen:  # Seen and filtered by the morphology (if there is one)
            return UNK_TAG_TRANS, tags, lambda tag, prev_tags: word_prob_model.log_prob(prev_tags + [tag[0]], word_form,
                                                                                        self.conf.UNKNOWN_VALUE)
        elif len(tags) == 1:  # Single anal (or eos): morphology filtering as the only common anal or seen only one anal
            UNK_TAG_TRANS = 0.0  # We are sure! P = 1 -> log(P) = 0.0
            return UNK_TAG_TRANS, tags, lambda _, __: self.conf.SINGLE_EMISSION_PROB
        elif len(tags) > 0:  # VOC not OOV (in vocabulary): the (morphology filtered) training set knows better...
            # Emission prob: tagprob - tag_apriori_prob (If not seen: UNK - 0)
            return UNK_TAG_TRANS, tags, lambda tag, _: guesser.tag_log_probability(lword, tag[0],
                                                                                   self.conf.UNKNOWN_VALUE) \
                                                        - self.model.tag_transition_model.apriori_log_prob(tag[0], 0.0)
        else:  # OOV: Guessed OOV (Do not have any clue. No tags yet!)
            # Emission prob: tag_prob - tag_apriori_prob (If not seen: UNK - 0)
            tags = guesser.tag_log_probabilities_w_max(lword, self.max_guessed_tags, self.suf_theta)
            return UNK_TAG_TRANS, tags, lambda tag, _: tag[1] - self.model.tag_transition_model.apriori_log_prob(tag[0],
                                                                                                                 0.0)

    def decode(self, observations: list, results_num: int, user_anals: list) -> list:
        # This is called from outside: Creates max_res_num peace of tag-sequence for the input sentence (observations)
        observations = list(observations)  # todo: Why we need this?
        if len(observations) == 0:
            return []
        observations.append(self.conf.EOS_TOKEN)  # Adds an End-of-Sentence token to the end of the sentence.

        start = NGram([self.model.bos_index for _ in range(self.model.tagging_order)], self.model.tagging_order)
        beam = {start: Node(start, 0.0, None)}  # beam {NGram -> Node}
        for pos, obs in enumerate(observations):         # obs: str
            new_beam = dict()            # {NGram -> Node}
            UNK_TAG_TRANS, tags, emission_prob_fun = self.next_probs(obs, pos, user_anals)
            # For every pev_tag list combined with every tag compute probs...
            for context in beam.keys():  # {NGram}  # {NGram -> {int -> (float, float)}}
                for tag in tags:
                    next_tag = tag[0]
                    new_state = context.add(next_tag)  # NGram
                    from_node = beam[context]          # Node

                    trans_prob = self.model.tag_transition_model.log_prob(context.token_list, next_tag, UNK_TAG_TRANS)
                    obs_prob = emission_prob_fun(tag, context.token_list)
                    new_weight = from_node.weight + trans_prob + obs_prob  # adding trans. and observation probabilities

                    # Update: Set or "update if more optimal": add if there is not a similar(*) ending Ngram in it.
                    # (*) Only the last n element is checked for equality! todo változik?
                    if new_state not in new_beam.keys():
                        new_beam[new_state] = Node(new_state, new_weight, from_node)
                    elif new_beam[new_state].weight < new_weight:  # Update if...
                        new_beam[new_state].prev = from_node
                        new_beam[new_state].weight = new_weight

            # Prune (newbeam -> Beam)
            if self.beam_size > 0:  # todo: better representation!
                beam = dict(sorted(new_beam.items(), key=lambda x: x[1].weight, reverse=True)[:self.beam_size])
            else:  # Do not add nodes under a specific treshold (computed from the maximal weight) to the beam.
                max_node_weight = max(n.weight for n in new_beam.values())
                beam = {ngram: act_node for ngram, act_node in new_beam.items()
                        if act_node.weight >= max_node_weight - self.log_theta}

        # Find max
        sorted_nodes = sorted(beam.values(), key=lambda n: n.weight)  # [Node]
        tag_seq_list = []
        for _ in range(results_num):  # k-top, k = results_num
            if len(sorted_nodes) == 0:
                break
            max_node = sorted_nodes.pop()
            # Decompose
            max_tag_seq = []
            prev = max_node
            act = max_node.prev
            while prev is not None:
                max_tag_seq.insert(0, act.state.last())
                act = prev
                prev = act.prev

            tag_seq_list.append((max_tag_seq[:-1], max_node.weight))  # Strip 'End of Sentence' tag
        return tag_seq_list  # [element]: [([int],float)]
