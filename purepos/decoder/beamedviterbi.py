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

    def next_probs(self, prev_tags_set: set, word: str, position: int, user_anals: list) -> dict:
        # A szóhoz tartozó tag-valószínűségeket gyűjti ki.
        # A token tulajdonságai határozzák meg a konkrét fv-t.
        if word == self.conf.EOS_TOKEN:
            # Next for eos token by all prev tags
            return {prev_tags: self.next_for_eos_token(prev_tags, None, None, None, None, None)
                    for prev_tags in prev_tags_set}

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
                word_prob_model = user_anals[position]
                seen = True  # If no probabilities, handle it like the morphological analyser (but without filtering)
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

        if seen:  # Seen and filtered by the morphology (if there is one)
            comp_tag_probs = self.next_for_seen_token
        elif len(tags) == 1:  # Single anal: morphology filtering as the only common anal or seen only one anal
            comp_tag_probs = self.next_for_single_tagged_token
        elif len(tags) > 0:  # Not OOV (in vocabulary): the morphology filtered training set knows better...
            comp_tag_probs = self.next_for_guessed_voc_token
        else:  # OOV (guessed): do not have any clue...
            comp_tag_probs = self.next_for_guessed_oov_token

        # For every pev_tag list combined with every tag compute probs...
        return {prev_tags: comp_tag_probs(prev_tags, word_form, lword, word_prob_model, guesser, tags)
                for prev_tags in prev_tags_set}

    def next_for_seen_token(self, prev_tags, word_form, __, word_prob_model, ____, tags):
        tag_probs = dict()  # Seen...
        for tag in tags:
            transion_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, tag,
                                                                     self.conf.UNKNOWN_TAG_TRANSITION)
            emission_prob = word_prob_model.log_prob(prev_tags.token_list + [tag], word_form, self.conf.UNKNOWN_VALUE)
            tag_probs[tag] = (transion_prob, emission_prob)
        return tag_probs

    def next_for_single_tagged_token(self, prev_tags, _, __, ___, ____, tags):  # Single anal...
        tag = tags[0]
        transion_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, tag, 0.0)
        emission_prob = 0.0  # We are sure! P = 1 -> log(P) = 0.0
        return {tag: (transion_prob, emission_prob)}

    def next_for_guessed_voc_token(self, prev_tags, _, lword, ___, guesser, tags):
        tag_probs = dict()  # VOC: Not OOV (Morphology or the training set knows better...)
        for tag in tags:  # Mapping is made one level lower...
            transion_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, tag,
                                                                     self.conf.UNKNOWN_TAG_TRANSITION)
            # Emission prob: tagprob - tag_apriori_prob (If not seen: UNK - 0)
            emission_prob = guesser.tag_log_probability(lword, tag, self.conf.UNKNOWN_VALUE) \
                            - self.model.tag_transition_model.apriori_log_prob(tag, 0.0)
            tag_probs[tag] = (transion_prob, emission_prob)
        return tag_probs

    def next_for_guessed_oov_token(self, prev_tags, _, lword, ___, guesser, _____):
        tag_probs = dict()  # OOV: Guessed OOV (Do not have any clue.)
        for tag, tag_prob in guesser.tag_log_probabilities_w_max(lword, self.max_guessed_tags,
                                                                 self.suf_theta):
            transion_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, tag,
                                                                     self.conf.UNKNOWN_TAG_TRANSITION)
            # Emission prob: tag_prob - tag_apriori_prob (If not seen: UNK - 0)
            emission_prob = tag_prob - self.model.tag_transition_model.apriori_log_prob(tag, 0.0)
            tag_probs[tag] = (transion_prob, emission_prob)
        return tag_probs

    def next_for_eos_token(self, prev_tags, _, __, ___, ____, _____):
        transion_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, self.model.eos_index,
                                                                 self.conf.UNKNOWN_VALUE)
        emission_prob = self.conf.EOS_EMISSION_PROB
        return {self.model.eos_index: (transion_prob, emission_prob)}

    def decode(self, observations: list, results_num: int, user_anals: list) -> list:
        # Ez a lényeg, ezt hívuk meg kívülről.
        # A modathoz (observations) max_res_num-nyi tag-listát készít
        # A mondathoz hozzáfűz egy <MONDATVÉGE> tokent.
        observations = list(observations)
        if len(observations) == 0:
            return []
        observations.append(self.conf.EOS_TOKEN)

        start = NGram([self.model.bos_index for _ in range(self.model.tagging_order)], self.model.tagging_order)
        # Maga az algoritmus  # beam {NGram -> Node}
        beam = {start: Node(start, 0.0, None)}
        pos = 0
        for obs in observations:         # obs: str
            new_beam = dict()            # {NGram -> Node}
            next_probs = dict()          # table: {(NGram, int) -> float} trololo :)
            obs_probs = dict()           # {NGram -> float}
            contexts = set(beam.keys())  # {NGram}  # {NGram -> {int -> (float, float)}}
            # XXX Innentől az 'adding observation probabilities'-al bezárólag egy ciklusban nem lenne jobb?
            for context, next_context_probs in self.next_probs(contexts, obs, pos, user_anals).items():
                for tag, (trans_prob, obs_prob) in next_context_probs.items():    # {int -> (float, float)}.items()
                    # context: NGram,
                    # next_context_probs: {int -> (float, float)}
                    next_probs[(context, tag)], obs_probs[context.add(tag)] = trans_prob, obs_prob
            # NGram, int
            for (context, next_tag), trans_val in next_probs.items():    # {(NGram, int) -> float}.items()
                new_state = context.add(next_tag)   # NGram
                from_node = beam[context]           # Node
                new_weight = trans_val + from_node.weight  # float
                # Update: Set or "update if more optimal" todo változik?
                # Hozzá veszi, ha nincs benn ilyen végű(*) tag sorozat.
                # (*) Csak at utolsó két elemet veszi figyelembe az egyezésvizsgálatkor!
                if new_state not in new_beam.keys():
                    new_beam[new_state] = Node(new_state, new_weight, from_node)
                elif new_beam[new_state].weight < new_weight:  # Update if...
                    new_beam[new_state].prev = from_node
                    new_beam[new_state].weight = new_weight

            # adding observation probabilities
            if len(next_probs) > 1:
                for tag_seq in new_beam.keys():     # {NGram -> Node}.keys()
                    new_beam[tag_seq].weight += obs_probs[tag_seq]

            # Prune (newbeam -> Beam)
            if self.beam_size > 0:  # todo: better representation!
                beam = dict(sorted(new_beam.items(), key=lambda x: x[1].weight, reverse=True)[:self.beam_size])
            else:
                # Egy küszöb súly alatti node-okat nem veszi be a beam-be.
                # A küszöböt a max súlyú node-ból számolja ki.
                max_node_weight = max(n.weight for n in new_beam.values())
                beam = {ngram: act_node for ngram, act_node in new_beam.items()
                        if act_node.weight >= max_node_weight - self.log_theta}
            pos += 1
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
