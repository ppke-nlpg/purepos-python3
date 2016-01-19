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

import math
from purepos.common.analysisqueue import analysis_queue
from purepos.common.spectokenmatcher import SpecTokenMatcher
from purepos.morphology import BaseMorphologicalAnalyser
from purepos.model.model import Model
from purepos.decoder.ngram import NGram
from purepos.model.probmodel import BaseProbabilityModel
from purepos.model.history import History

# „enum” values
SEEN = 0
LOWER_CASED_SEEN = 1
SPECIAL_TOKEN = 2
UNSEEN = 3

EOS_EMISSION_PROB = 1.0
UNKNOWN_TAG_WEIGHT = -99.0
UNKOWN_TAG_TRANSITION = -99.0
UNKNOWN_VALUE = -99.0
TAB = "\t"  # ez eredetileg field volt.


class Node:
    def __init__(self, state: NGram, weight: float, previous: NGram or None):
        self.state = state
        self.weight = weight
        self.prev = previous

    def __str__(self):
        return "{state: {}, weight: {}}".format(str(self.state), str(self.weight))


class BaseDecoder:
    def __init__(self, model: Model,
                 morphological_analyzer: BaseMorphologicalAnalyser,
                 log_theta: float,
                 suf_theta: float,
                 max_guessed_tags: int):
        self.model = model
        self.morphological_analyzer = morphological_analyzer
        self.log_theta = log_theta
        self.suf_theta = suf_theta
        self.max_guessed_tags = max_guessed_tags
        self.tags = model.tag_vocabulary.tag_indices()
        self.spectoken_matcher_match_lexical_element = SpecTokenMatcher().match_lexical_element

    def decode(self, observations: list, max_res_num: int) -> list:
        pass

    def next_probs(self, prev_tags_set: set, word: str, position: int, is_first: bool) -> dict:
        # A szóhoz tartozó tag-valószínűségeket gyűjti ki.
        # A token tulajdonságai határozzák meg a konkrét fv-t.
        if word == Model.EOS_TOKEN:
            # Next for eos token by all prev tags
            return {prev_tags: {self.model.eos_index: (self.model.tag_transition_model.log_prob(prev_tags.token_list,
                                                                                                self.model.eos_index),
                                                       EOS_EMISSION_PROB)}
                    for prev_tags in prev_tags_set}

        lword = word.lower()
        isupper = not (lword == word)
        anals = []
        isoov = True
        # seen = NOT_SPECIFIED
        word_prob_model = BaseProbabilityModel()
        word_form = word
        # tags = set()
        is_spec = False
        # spec_name = ""

        str_anals = self.morphological_analyzer.tags(word)
        if len(str_anals) > 0:
            isoov = False
            for tag in str_anals:
                i = self.model.tag_vocabulary.index(tag)
                if i is not None:
                    anals.append(i)
                else:
                    anals.append(self.model.tag_vocabulary.add_element(tag))

        tags = self.model.standard_tokens_lexicon.tags(word)
        if len(tags) > 0:
            word_prob_model = self.model.standard_emission_model
            word_form = word
            seen = SEEN
        else:
            tags = self.model.standard_tokens_lexicon.tags(lword)
            if is_first and isupper and len(tags) > 0:
                word_prob_model = self.model.standard_emission_model
                word_form = lword
                seen = LOWER_CASED_SEEN
            else:
                spec_name = self.spectoken_matcher_match_lexical_element(word)
                is_spec = (spec_name is not None)
                if is_spec:
                    word_prob_model = self.model.spec_tokens_emission_model
                    tags = self.model.spec_tokens_lexicon.tags(spec_name)
                    if len(tags) > 0:
                        seen = SPECIAL_TOKEN
                    else:
                        seen = UNSEEN
                    word_form = spec_name
                else:
                    seen = UNSEEN
        user_anals = analysis_queue
        if user_anals.has_anal(position):
            new_tags = user_anals.tags(position, self.model.tag_vocabulary)
            if user_anals.use_probabilities(position):
                new_word_model = user_anals.lexical_model_for_word(position, self.model.tag_vocabulary)
                return self.next_for_seen_token(prev_tags_set, new_word_model, word_form, is_spec, new_tags, anals)
            else:
                if seen != UNSEEN:
                    return self.next_for_seen_token(prev_tags_set, word_prob_model, word_form, is_spec, new_tags, anals)
                else:
                    if len(new_tags) == 1:
                        return self.next_for_single_tagged_token(prev_tags_set, new_tags)
                    else:
                        return self.next_for_guessed_token(prev_tags_set, lword, isupper, new_tags, False)
        else:
            if seen != UNSEEN:
                return self.next_for_seen_token(prev_tags_set, word_prob_model, word_form, is_spec, tags, anals)
            else:
                if len(anals) == 1:
                    return self.next_for_single_tagged_token(prev_tags_set, anals)
                else:
                    return self.next_for_guessed_token(prev_tags_set, lword, isupper, anals, isoov)

    def next_for_seen_token(self, prev_tags_set: set, word_prob_model: BaseProbabilityModel, word_form: str, _: bool,
                            tags: set, anals: list):  # _ : bool is_seen
        mapper = word_prob_model.context_mapper
        # Filter tags with morphology
        tagset = tags
        if anals is not None:
            if mapper is not None:
                common = set(mapper.filter(anals, tags))
            else:
                common = set(anals)
                common = common.intersection(tags)
            if len(common) > 0:
                tagset = common

        ret = dict()
        for prev_tags in prev_tags_set:
            tag_probs = dict()
            for tag in tagset:
                tag_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, tag)
                act_tags = list(prev_tags.token_list)
                act_tags.append(tag)
                emission_prob = word_prob_model.log_prob(act_tags, word_form)
                # ez nem kell, mert nem -inf lesz, hanem 99
                # if tag_prob == float("-inf"):
                #     tag_prob = UNKOWN_TAG_TRANSITION
                # if emission_prob == float("-inf"):
                #     emission_prob = UNKNOWN_TAG_WEIGHT
                tag_probs[tag] = (tag_prob, emission_prob)
            ret[prev_tags] = tag_probs
        return ret

    def next_for_guessed_token(self, prev_tags_set: set, word_form: str, upper: bool, anals: list or set, oov: bool)\
            -> dict:
        if upper:
            guesser = self.model.upper_case_suffix_guesser
        else:
            guesser = self.model.lower_case_suffix_guesser
        if not oov:
            rrr = dict()
            tag_probs = dict()
            for tag in anals:
                # XXX There is even not mapper defined...
                new_tag = guesser.mapper.map(tag)
                if new_tag > self.model.tag_vocabulary.max_index():
                    emission_prob = UNKNOWN_TAG_WEIGHT
                    transition_prob = UNKOWN_TAG_TRANSITION
                    tag_probs[tag] = (transition_prob, emission_prob)
                    for prev_tags in prev_tags_set:
                        rrr[prev_tags] = tag_probs
                else:
                    tag_log_prob = guesser.tag_log_probability(word_form, tag)
                    if tag_log_prob == UNKNOWN_VALUE:
                        emission_prob = UNKNOWN_TAG_WEIGHT
                    else:
                        emission_prob = tag_log_prob - math.log(self.model.apriori_tag_probs[new_tag])
                    for prev_tags in prev_tags_set:
                        transition_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, tag)
                        tag_probs[tag] = (transition_prob, emission_prob)
                        rrr[prev_tags] = tag_probs
            return rrr

        else:
            # Next for guessed oov token
            rrr = dict()
            tag_probs = dict()
            guessed_tags = guesser.tag_log_probabilities(word_form)
            # Prune guessed tags
            # A legnagyobb valószínűségű tag-eket kiszedi, hogy az ismeretlen szavak taggelésénél ne
            # vezessenek félre. // „TnT – A Statistical Part-of-Speech Tagger” Brants, Thorsen 2000, 2.3, 4)
            pruned_guessed_tags = set()
            max_tag = max(guessed_tags.items(), key=lambda x: x[1])[0]  # Max probability tag
            max_val = guessed_tags[max_tag]
            min_val = max_val - self.suf_theta
            for k, v in guessed_tags.items():
                if v > min_val:
                    pruned_guessed_tags.add((k, v))
            if len(pruned_guessed_tags) > self.max_guessed_tags:
                l = list(pruned_guessed_tags)
                l.sort(key=lambda ent: ent[1], reverse=True)
                for e in l:
                    if len(pruned_guessed_tags) <= self.max_guessed_tags:
                        break
                    pruned_guessed_tags.remove(e)

            for prev_tags in prev_tags_set:
                for guess in pruned_guessed_tags:
                    emission_prob = guess[1]
                    tag = guess[0]
                    tag_trans_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, tag)
                    apriori_prob = math.log(self.model.apriori_tag_probs[tag])
                    tag_probs[tag] = (tag_trans_prob, emission_prob - apriori_prob)
                rrr[prev_tags] = tag_probs
            return rrr

    def next_for_single_tagged_token(self, prev_tags_set: set, anals: list or set) -> dict:
        rrr = dict()
        for prev_tags in prev_tags_set:
            tag_probs = dict()
            # tag = anals[0]. Ez setre és listre is működik.
            tag = anals.__iter__().__next__()
            tag_prob = self.model.tag_transition_model.log_prob(prev_tags.token_list, tag)
            # Itt nem -99 a default, hanem 0
            tag_prob = tag_prob if tag_prob != UNKNOWN_VALUE else 0
            tag_probs[tag] = (tag_prob, 0.0)
            rrr[prev_tags] = tag_probs
        return rrr


class BeamSearch(BaseDecoder):
    # BeamSearch algorithm.
    # Nincs tesztelve.
    def __init__(self, model: Model, morph_analyser: BaseMorphologicalAnalyser, log_theta: float,
                 suf_theta: float, max_guessed_tags: int, beam_size: int=None):
        if beam_size is None:
            self.beam_size = 10
            self.fixed_beam = False
        else:
            log_theta = 0
            self.beam_size = beam_size
            self.fixed_beam = True
        super().__init__(model, morph_analyser, log_theta, suf_theta, max_guessed_tags)

    def decode(self, observations: list, max_res_num: int) -> list:
        # A mondathoz hozzáfűz egy <MONDATVÉGE> tokent.
        observations = list(observations)
        observations.append(Model.EOS_TOKEN)

        # The actual beam search
        # Init beam
        # NÖVEKVŐ SORREND LESZ! [0, 1, 2, 3, 4 ...]
        start = NGram([self.model.bos_index for _ in range(0, self.model.tagging_order)], self.model.tagging_order)
        beam = [History(start, 0.0)]
        # beam search main
        position = 0
        for word in observations:
            contexts = {h.tag_seq for h in beam}  # collect contexts
            probs = self.next_probs(contexts, word, position, (position == 0))
            # Update beam
            new_beam = []
            for h in beam:
                context = h.tag_seq
                old_prob = h.log_prob
                transitions = probs[context]
                for next_tag, prob_vals in transitions.items():
                    new_seq = context.add(next_tag)
                    new_prob = old_prob + prob_vals[0] + prob_vals[1]
                    new_beam.append(History(new_seq, new_prob))
            beam = new_beam.sort()
            # Prune
            if self.fixed_beam:
                beam[:-self.beam_size] = []  # trololo :)
            else:
                maxh = beam[-1]
                while not beam[0].log_prob > (maxh.log_prob - self.log_theta):
                    beam[0:1] = []
            position += 1
        # k-top
        ret = []
        for i in range(min(max_res_num, len(beam))):
            # h = beam[-1]
            # beam[-1:] = []
            h = beam.pop()
            tag_seq = h.tag_seq.token_list
            cleaned = tag_seq[self.model.tagging_order:]
            ret.append((cleaned, h.log_prob))
        return ret

# def create_initial_element(self) -> NGram:
#     pass


class BeamedViterbi(BaseDecoder):
    def __init__(self, model: Model, morph_analyser: BaseMorphologicalAnalyser, log_theta: float,
                 suf_theta: float, max_guessed_tags: int):
        super().__init__(model, morph_analyser, log_theta, suf_theta, max_guessed_tags)

    def decode(self, observations: list, results_num: int) -> list:
        # Ez a lényeg, ezt hívuk meg kívülről.
        # A modathoz (observations) max_res_num-nyi tag-listát készít
        # A mondathoz hozzáfűz egy <MONDATVÉGE> tokent.
        observations = list(observations)
        observations.append(Model.EOS_TOKEN)

        start = NGram([self.model.bos_index for _ in range(0, self.model.tagging_order)], self.model.tagging_order)
        # Maga az algoritmus  # beam {NGram -> Node}
        beam = {start: Node(start, 0.0, None)}
        first = True
        pos = 0
        for obs in observations:         # obs: str
            new_beam = dict()            # {NGram -> Node}
            next_probs = dict()          # table: {(NGram, int) -> float} trololo :)
            obs_probs = dict()           # {NGram -> float}
            contexts = set(beam.keys())  # {NGram}
            nexts = self.next_probs(contexts, obs, pos, first)  # {NGram -> {int -> (float, float)}}
            for context, next_context_probs in nexts.items():
                for tag, pair in next_context_probs.items():    # {int -> (float, float)}.items()
                    # context: NGram,
                    # next_context_probs: {int -> (float, float)}
                    obs_probs[context.add(tag)], next_probs[(context, tag)] = pair

            for cell_index, trans_val in next_probs.items():    # {(NGram, int) -> float}.items()
                context, next_tag = cell_index            # NGram, int
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

            # Prune
            # Egy küszöb súly alatti node-okat nem veszi be a beam-be.
            # A küszöböt a max súlyú node-ból számolja ki.
            max_node_weight = max(n.weight for n in beam.values())
            beam = {ngram: act_node for ngram, act_node in beam.items()
                    if act_node.weight >= max_node_weight - self.log_theta}
            first = False
            pos += 1
        # Find max
        sorted_nodes = sorted(beam.values(), key=lambda n: n.weight)  # [Node]
        tag_seq_list = []
        for i in range(results_num):
            if len(sorted_nodes) == 0:
                break
            max_node = sorted_nodes.pop()
            # Decompose
            max_tag_seq = list()
            prev, act = max_node.prev, max_node
            while prev is not None:
                max_tag_seq.append(act.state.last())  # We must reverse the list!
                prev, act = act.prev, prev
            tag_seq_list.append((max_tag_seq[::-1], max_node.weight))  # Reverse here!
        # Clean results
        # A taglistákról leszedi az utolsó, MONDATVÉGE token tag-jét.
        # XXX Esetleg ezt lehetne begyúrni az előző ciklusba?
        return [(element[0][:-1], element[1]) for element in tag_seq_list]  # [element]: [([int],float)]
