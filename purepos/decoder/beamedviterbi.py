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

from purepos.common.analysisqueue import analysis_queue
from purepos.common.spectokenmatcher import SpecTokenMatcher
from purepos.morphology import BaseMorphologicalAnalyser
from purepos.model.model import Model
from purepos.decoder.ngram import NGram

EOS_EMISSION_PROB = 1.0
UNKNOWN_TAG_WEIGHT = -99.0
UNKOWN_TAG_TRANSITION = -99.0


class Node:
    def __init__(self, state: NGram, weight: float, previous: NGram or None):
        self.state = state
        self.weight = weight
        self.prev = previous

    def __str__(self):
        return "{state: {}, weight: {}}".format(str(self.state), str(self.weight))


class BeamedViterbi:
    def __init__(self, model: Model, morphological_analyzer: BaseMorphologicalAnalyser, log_theta: float,
                 suf_theta: float, max_guessed_tags: int, beam_size: int=None):
        self.model = model
        self.morphological_analyzer = morphological_analyzer
        self.log_theta = log_theta
        self.suf_theta = suf_theta
        self.max_guessed_tags = max_guessed_tags
        self.beam_size = beam_size
        self.tags = model.tag_vocabulary.tag_indices()
        self.spectoken_matcher_match_lexical_element = SpecTokenMatcher().match_lexical_element
        self.user_anals = analysis_queue

    def next_probs(self, prev_tags_set: set, word: str, position: int) -> dict:
        # A szóhoz tartozó tag-valószínűségeket gyűjti ki.
        # A token tulajdonságai határozzák meg a konkrét fv-t.
        if word == Model.EOS_TOKEN:
            # Next for eos token by all prev tags
            rrr = dict()
            for prev_tags in prev_tags_set:
                transion_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, self.model.eos_index)
                emission_prob = EOS_EMISSION_PROB
                rrr[prev_tags] = {self.model.eos_index: (transion_prob, emission_prob)}
            return rrr

        # Defaults:
        # word_prob_model = spec_tokens_emission_model | spec_tokens_emission_model
        # tags = standard_token_lexicon | spec_tokens_lexicon
        word_form = word
        lword = word.lower()
        isupper = not (lword == word)
        word_prob_model = self.model.standard_emission_model
        tags = self.model.standard_tokens_lexicon.tags(word)
        anals = [self.model.tag_vocabulary.add_element(tag) for tag in self.morphological_analyzer.tags(word)]
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
                isupper = False  # todo: Maybe to use both lower and uppercased guessers for unseen...
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
                        # else SPECIAL UNSEEN -> UNSEEN XXX why?

        # Set guesser for casing of word_form...
        if isupper:
            guesser = self.model.upper_suffix_tree
        else:
            guesser = self.model.lower_suffix_tree

        # User's own stuff... May overdefine (almost) everything... (left as is: isupper, lword, wordform)
        if self.user_anals.has_anal(position):
            anals = self.user_anals.tags(position, self.model.tag_vocabulary)
            if self.user_anals.use_probabilities(position):
                word_prob_model = self.user_anals.lexical_model_for_word(position, self.model.tag_vocabulary)
                seen = True
                tags = anals  # Here is the same
        else:  # User's anals do not need filtering...
            # Filter tags with morphology (tags = tags & anals )
            mapper = word_prob_model.context_mapper
            if anals is not None:
                if mapper is not None:
                    common = set(mapper.filter(anals, tags))
                else:
                    common = set(anals)
                    common = common.intersection(tags)
                if len(common) > 0:
                    anals = common

        # For every pev_tag list combined with every tag compute probs...
        rrr = dict()
        for prev_tags in prev_tags_set:
            tag_probs = dict()
            if seen:
                for tag in tags:
                    transion_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, tag)
                    emission_prob = word_prob_model.log_prob(prev_tags.token_list + [tag], word_form)
                    tag_probs[tag] = (transion_prob, emission_prob)
            elif len(anals) == 1:  # Single anal...
                tag = anals[0]  # tag = anals[0]. Unified for set and list: anals.__iter__().__next__()
                transion_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, tag, 0.0)
                emission_prob = 0.0  # We are sure! P = 1 -> log(P) = 0.0
                tag_probs[tag] = (transion_prob, emission_prob)

            elif len(anals) > 0:  # Not OOV (Morphology or the training set knows better...)
                for tag in anals:  # Mapping is made one level lower...
                    transion_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, tag,
                                                                             UNKOWN_TAG_TRANSITION)
                    # Emission prob: tagprob - tag_apriori_prob (If not seen: UNK - 0)
                    emission_prob = guesser.tag_log_probability(lword, tag, UNKNOWN_TAG_WEIGHT) \
                                    - self.model.apriori_tag_probs.log_prob(tag, 0.0)
                    tag_probs[tag] = (transion_prob, emission_prob)

            else:  # Guessed OOV (Do not have any clue.)
                for tag, tag_prob in guesser.tag_log_probabilities_w_max(lword, self.max_guessed_tags, self.suf_theta):
                    transion_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, tag)
                    # Emission prob: tag_prob - tag_apriori_prob (If not seen: UNK - 0)
                    emission_prob = tag_prob - self.model.apriori_tag_probs.log_prob(tag, 0.0)
                    tag_probs[tag] = (transion_prob, emission_prob)
            rrr[prev_tags] = tag_probs
        return rrr

    def decode(self, observations: list, results_num: int) -> list:
        # Ez a lényeg, ezt hívuk meg kívülről.
        # A modathoz (observations) max_res_num-nyi tag-listát készít
        # A mondathoz hozzáfűz egy <MONDATVÉGE> tokent.
        observations = list(observations)
        if len(observations) == 0:
            return []
        observations.append(Model.EOS_TOKEN)

        start = NGram([self.model.bos_index for _ in range(self.model.tagging_order)], self.model.tagging_order)
        # Maga az algoritmus  # beam {NGram -> Node}
        beam = {start: Node(start, 0.0, None)}
        pos = 0
        for obs in observations:         # obs: str
            new_beam = dict()            # {NGram -> Node}
            next_probs = dict()          # table: {(NGram, int) -> float} trololo :)
            obs_probs = dict()           # {NGram -> float}
            contexts = set(beam.keys())  # {NGram}  # {NGram -> {int -> (float, float)}}
            for context, next_context_probs in self.next_probs(contexts, obs, pos).items():
                for tag, pair in next_context_probs.items():    # {int -> (float, float)}.items()
                    # context: NGram,
                    # next_context_probs: {int -> (float, float)}
                    next_probs[(context, tag)], obs_probs[context.add(tag)] = pair
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
