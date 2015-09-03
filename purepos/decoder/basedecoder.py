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
from purepos.common.spectokenmatcher import SpecTokenMatcher
from purepos.common import util
from purepos.morphology import BaseMorphologicalAnalyser
from purepos.model.rawmodel import CompiledModel
from purepos.model.mapper import TagMapper
from purepos.model.ngram import NGram
from purepos.model.modeldata import ModelData
from purepos.model.probmodel import BaseProbabilityModel
from purepos.model.suffixguesser import BaseSuffixGuesser, HashSuffixGuesser
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
    def __init__(self, model: CompiledModel,
                 morphological_analyzer: BaseMorphologicalAnalyser,
                 log_theta: float,
                 suf_theta: float,
                 max_guessed_tags: int):
        self.model = model
        self.morphological_analyzer = morphological_analyzer
        self.log_theta = log_theta
        self.suf_theta = suf_theta
        self.max_guessed_tags = max_guessed_tags
        self.tags = model.data.tag_vocabulary.tag_indices()

    def next_probs(self, prev_tags_set: set, word: str, position: int, is_first: bool) -> dict:
        # A szóhoz tartozó tag-valószínűségeket gyűjti ki.
        # A token tulajdonságai határozzák meg a konkrét fv-t.
        spectoken_matcher = SpecTokenMatcher()
        if word == ModelData.EOS_TOKEN:
            return self.next_for_eos_token(prev_tags_set)

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
                i = self.model.data.tag_vocabulary.index(tag)
                if i is not None:
                    anals.append(i)
                else:
                    anals.append(self.model.data.tag_vocabulary.add_element(tag))

        tags = self.model.data.standard_tokens_lexicon.tags(word)
        if len(tags) > 0:
            word_prob_model = self.model.compiled_data.standard_emission_model
            word_form = word
            seen = SEEN
        else:
            tags = self.model.data.standard_tokens_lexicon.tags(lword)
            if is_first and isupper and len(tags) > 0:
                word_prob_model = self.model.compiled_data.standard_emission_model
                word_form = lword
                seen = LOWER_CASED_SEEN
            else:
                spec_name = spectoken_matcher.match_lexical_element(word)
                is_spec = (spec_name is not None)
                if is_spec:
                    word_prob_model = self.model.compiled_data.spec_tokens_emission_model
                    tags = self.model.data.spec_tokens_lexicon.tags(spec_name)
                    if len(tags) > 0:
                        seen = SPECIAL_TOKEN
                    else:
                        seen = UNSEEN
                    word_form = spec_name
                else:
                    seen = UNSEEN
        user_anals = util.analysis_queue
        if user_anals.has_anal(position):
            new_tags = user_anals.tags(position, self.model.data.tag_vocabulary)
            if user_anals.use_probabilities(position):
                new_word_model = user_anals.lexical_model_for_word(position,
                                                                   self.model.data.tag_vocabulary)
                return self.next_for_seen_token(prev_tags_set, new_word_model, word_form,
                                                is_spec, new_tags, anals)
            else:
                if seen != UNSEEN:
                    return self.next_for_seen_token(prev_tags_set, word_prob_model, word_form,
                                                    is_spec, new_tags, anals)
                else:
                    if len(new_tags) == 1:
                        return self.next_for_single_tagged_token(prev_tags_set, new_tags)
                    else:
                        return self.next_for_guessed_token(prev_tags_set, lword, isupper,
                                                           new_tags, False)
        else:
            if seen != UNSEEN:
                return self.next_for_seen_token(prev_tags_set, word_prob_model, word_form,
                                                is_spec, tags, anals)
            else:
                if len(anals) == 1:
                    return self.next_for_single_tagged_token(prev_tags_set, anals)
                else:
                    return self.next_for_guessed_token(prev_tags_set, lword, isupper, anals, isoov)

    def next_for_eos_token(self, prev_tags_set: set) -> dict:
        ret = dict()
        for prev_tags in prev_tags_set:
            eos_prob = self.model.compiled_data.tag_transition_model.log_prob(
                prev_tags.token_list, self.model.data.eos_index)
            r = dict()
            r[self.model.data.eos_index] = (eos_prob, EOS_EMISSION_PROB)
            ret[prev_tags] = r
        return ret

    def next_for_seen_token(self, prev_tags_set: set,
                            word_prob_model: BaseProbabilityModel,
                            word_form: str,
                            _: bool,  # is_seen
                            tags: set,
                            anals: list):
        tagset = self.filter_tags_with_morphology(tags, anals, word_prob_model.context_mapper)
        ret = dict()
        for prev_tags in prev_tags_set:
            tag_probs = dict()
            for tag in tagset:
                tag_prob = self.model.compiled_data.tag_transition_model.log_prob(
                    prev_tags.token_list, tag)
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

    def next_for_guessed_token(self, prev_tags_set: set,
                               word_form: str,
                               upper: bool,
                               anals: list or set,
                               oov: bool) -> dict:
        if upper:
            guesser = self.model.compiled_data.upper_case_suffix_guesser
        else:
            guesser = self.model.compiled_data.lower_case_suffix_guesser
        if not oov:
            return self.next_for_guessed_voc_token(prev_tags_set, word_form, anals, guesser)
        else:
            return self.next_for_guessed_oov_token(prev_tags_set, word_form, guesser)

    def next_for_guessed_oov_token(self, prev_tags_set: set,
                                   lword: str,
                                   guesser: BaseSuffixGuesser):
        rrr = dict()
        tag_probs = dict()
        guessed_tags = guesser.tag_log_probabilities(lword)
        pruned_guessed_tags = self.prune_guessed_tags(guessed_tags)
        for prev_tags in prev_tags_set:
            for guess in pruned_guessed_tags:
                emission_prob = guess[1]
                tag = guess[0]
                tag_trans_prob = self.model.compiled_data.tag_transition_model.log_prob(
                    prev_tags.token_list, tag)
                apriori_prob = math.log(self.model.compiled_data.apriori_tag_probs[tag])
                tag_probs[tag] = (tag_trans_prob, emission_prob - apriori_prob)
            rrr[prev_tags] = tag_probs
        return rrr

    def next_for_guessed_voc_token(self, prev_tags_set: set,
                                   lword: str,
                                   anals: list or set,
                                   guesser: HashSuffixGuesser) -> dict:
        rrr = dict()
        tag_probs = dict()
        possible_tags = anals
        for tag in possible_tags:
            new_tag = guesser.mapper.map(tag)
            if new_tag > self.model.data.tag_vocabulary.max_index():
                emission_prob = UNKNOWN_TAG_WEIGHT
                transition_prob = UNKOWN_TAG_TRANSITION
                tag_probs[tag] = (transition_prob, emission_prob)
                for prev_tags in prev_tags_set:
                    rrr[prev_tags] = tag_probs
            else:
                apriori_prob = self.model.compiled_data.apriori_tag_probs[new_tag]
                log_apriori_prob = math.log(apriori_prob)
                tag_log_prob = guesser.tag_log_probability(lword, tag)
                if tag_log_prob == UNKNOWN_VALUE:
                    emission_prob = UNKNOWN_TAG_WEIGHT
                else:
                    emission_prob = tag_log_prob - log_apriori_prob
                for prev_tags in prev_tags_set:
                    transition_prob = self.model.compiled_data.tag_transition_model.log_prob(
                        prev_tags.token_list, tag)
                    tag_probs[tag] = (transition_prob, emission_prob)
                    rrr[prev_tags] = tag_probs
        return rrr

    def next_for_single_tagged_token(self, prev_tags_set: set,
                                     anals: list or set) -> dict:
        rrr = dict()
        for prev_tags in prev_tags_set:
            tag_probs = dict()
            # tag = anals[0]. Ez setre és listre is működik.
            tag = anals.__iter__().__next__()
            tag_prob = self.model.compiled_data.tag_transition_model.log_prob(
                prev_tags.token_list, tag)
            # Itt nem -99 a default, hanem 0
            tag_prob = tag_prob if tag_prob != UNKNOWN_VALUE else 0
            tag_probs[tag] = (tag_prob, 0.0)
            rrr[prev_tags] = tag_probs
        return rrr

    @staticmethod
    def filter_tags_with_morphology(tags: set,
                                    anals: list or set,
                                    mapper: TagMapper) -> set:
        if anals is not None:
            if mapper is not None:
                common = set(mapper.filter(anals, tags))
            else:
                common = set(anals)
                common = common.intersection(tags)
            if len(common) > 0:
                return common
        return tags

    def prune_guessed_tags(self, guessed_tags: dict) -> set:  # set of pairs
        # A legnagyobb valószínűségű tag-eket kiszedi, hogy az ismeretlen szavak taggelésénél ne
        # vezessenek félre. // „TnT – A Statistical Part-of-Speech Tagger” Brants, Thorsen 2000
        # 2.3, 4)
        s = set()
        max_tag = BaseSuffixGuesser.max_probability_tag(guessed_tags)
        max_val = guessed_tags[max_tag]
        min_val = max_val - self.suf_theta
        for k, v in guessed_tags.items():
            if v > min_val:
                s.add((k, v))
        if len(s) > self.max_guessed_tags:
            l = list(s)
            l.sort(key=lambda ent: ent[1], reverse=True)
            for e in l:
                if len(s) <= self.max_guessed_tags:
                    break
                s.remove(e)
        return s

    @staticmethod
    def decompose(node: Node) -> list:
        stack = list()
        act = node
        prev = node.prev
        while prev is not None:
            stack.insert(0, act.state.last())
            act = prev
            prev = act.prev
        return stack

    def decode(self, observations: list, max_res_num: int) -> list:
        pass

    @staticmethod
    def clean_results(tag_seq_list: list) -> list:  # [([int],float)]
        # A taglistákról leszedi az utolsó, MONDATVÉGE token tag-jét.
        ret = list()
        for element in tag_seq_list:                # element: ([int],float)
            tag_seq = element[0]                    # tag_seq: [int]
            new_tag_seq = tag_seq[:-1]              # new_tag_seq: [int]
            ret.append((new_tag_seq, element[1]))
        return ret

    @staticmethod
    def prepare_observations(observations: list) -> list:
        # A mondathoz hozzáfűz egy <MONDATVÉGE> tokent.
        obs = list(observations)
        obs.append(ModelData.EOS_TOKEN)
        return obs

    def create_initial_element(self) -> NGram:
        n = self.model.data.tagging_order
        start_tags = [self.model.data.bos_index for _ in range(0, n)]
        start_ngram = NGram(start_tags, self.model.data.tagging_order)
        return start_ngram

    @staticmethod
    def start_node(start: NGram) -> Node:
        return Node(start, 0.0, None)


class BeamSearch(BaseDecoder):
    # BeamSearch algorithm.
    # Nincs tesztelve.
    def __init__(self, model: CompiledModel,
                 morph_analyser: BaseMorphologicalAnalyser,
                 log_theta: float,
                 suf_theta: float,
                 max_guessed_tags: int,
                 beam_size: int=None):
        if beam_size is None:
            super().__init__(model, morph_analyser, log_theta, suf_theta, max_guessed_tags)
            self.beam_size = 10
            self.fixed_beam = False
        else:
            super().__init__(model, morph_analyser, 0, suf_theta, max_guessed_tags)
            self.beam_size = beam_size
            self.fixed_beam = True

    def decode(self, observations: list, max_res_num: int) -> list:
        observations = self.prepare_observations(observations)
        beam = self.beam_search(observations)
        return self.k_top(beam, max_res_num)

    def k_top(self, beam: list, max_res_num: int) -> list:
        ret = []
        for i in range(min(max_res_num, len(beam))):
            # h = beam[-1]
            # beam[-1:] = []
            h = beam.pop()
            tag_seq = h.tag_seq.token_list
            cleaned = self.clean(tag_seq)
            ret.append((cleaned, h.log_prob))
        return ret

    def clean(self, tag_seq: list) -> list:
        return tag_seq[self.model.data.tagging_order:]

    def beam_search(self, observations: list) -> list:
        beam = self.init_beam()
        position = 0
        for word in observations:
            contexts = self.collect_contexts(beam)
            probs = self.next_probs(contexts, word, position, (position == 0))
            beam = self.update_beam(beam, probs)
            self.prune(beam)
            position += 1
        return beam

    @staticmethod
    def collect_contexts(beam: list) -> set:
        return {h.tag_seq for h in beam}  # trololob :) inline?

    @staticmethod
    def update_beam(beam, probs: dict) -> list:
        new_beam = []
        for h in beam:
            context = h.tag_seq
            old_prob = h.log_prob
            transitions = probs[context]
            for next_tag, prob_vals in transitions.items():
                new_seq = context.add(next_tag)
                new_prob = old_prob + prob_vals[0] + prob_vals[1]
                new_beam.append(History(new_seq, new_prob))
        new_beam.sort()
        return new_beam

    def prune(self, beam: list):
        if self.fixed_beam:
            beam[:-self.beam_size] = []  # trololo :)
        else:
            maxh = beam[-1]
            while not beam[0].log_prob > (maxh.log_prob - self.log_theta):
                beam[0:1] = []

    def init_beam(self) -> list:
        beam = []
        init_ngram = self.create_initial_element()
        # NÖVEKVŐ SORREND LESZ! [0, 1, 2, 3, 4 ...]
        beam.append(History(init_ngram, 0.0))

# def create_initial_element(self) -> NGram:
#     pass


class BeamedViterbi(BaseDecoder):
    def __init__(self, model: CompiledModel,
                 morph_analyser: BaseMorphologicalAnalyser,
                 log_theta: float,
                 suf_theta: float,
                 max_guessed_tags: int):
        super().__init__(model, morph_analyser, log_theta, suf_theta, max_guessed_tags)

    def decode(self, observations: list, max_res_num: int) -> list:
        # Ez a lényeg, ezt hívuk meg kívülről.
        # A modathoz (observations) max_res_num-nyi tag-listát készít
        obs_sentence = self.prepare_observations(observations)
        start_ngram = self.create_initial_element()
        tag_seq_list = self.beamed_search(start_ngram, obs_sentence, max_res_num)
        return self.clean_results(tag_seq_list)  # [([int],float)]

    def beamed_search(self, start: NGram,
                      observations: list,  # [str]
                      results_num: int) -> list:
        # Maga az algoritmus
        beam = dict()                    # {NGram -> Node}
        beam[start] = self.start_node(start)
        first = True
        pos = 0
        for obs in observations:         # obs: str
            new_beam = dict()            # {NGram -> Node}
            next_probs = dict()          # table: {(NGram, int) -> float} trololo :)
            obs_probs = dict()           # {NGram -> float}
            contexts = set(beam.keys())  # {NGram}
            nexts = self.next_probs(contexts, obs, pos, first)  # {NGram -> {int -> (float, float)}}
            for context, next_context_probs in nexts.items():
                # context: NGram,
                # next_context_probs: {int -> (float, float)}
                for tag, pair in next_context_probs.items():    # {int -> (float, float)}.items()
                    next_probs[(context, tag)] = pair[0]
                    obs_probs[context.add(tag)] = pair[1]

            for cell_index, trans_val in next_probs.items():    # {(NGram, int) -> float}.items()
                next_tag = cell_index[1]            # int
                context = cell_index[0]             # NGram
                new_state = context.add(next_tag)   # NGram
                from_node = beam[context]           # Node
                new_val = trans_val + from_node.weight  # float
                self.update(new_beam, new_state, new_val, from_node)  # todo változik?
            # adding observation probabilities
            if len(next_probs) > 1:
                for tag_seq in new_beam.keys():     # {NGram -> Node}.keys()
                    # new_beam[tag_seq].weight += obs_probs[tag_seq]
                    node = new_beam[tag_seq]
                    obs_prob = obs_probs[tag_seq]
                    node.weight += obs_prob

            beam = self.prune(new_beam)
            first = False
            pos += 1
        return self.find_max(beam, results_num)  # [([int],float)]?

    def find_max(self, beam: dict,              # {NGram -> Node}
                 results_num: int) -> list:
        sorted_nodes = sorted(beam.values(), key=lambda node: node.weight)  # [Node]
        ret = []
        for i in range(results_num):
            if len(sorted_nodes) == 0:
                break
            max_node = sorted_nodes.pop()
            max_tag_seq = self.decompose(max_node)
            ret.append((max_tag_seq, max_node.weight))
        return ret  # [([int],float)]

    def prune(self, beam: dict) -> dict:
        # Egy küszöb súly alatti node-okat nem veszi be a beam-be.
        # A küszöböt a max súlyú node-ból számolja ki.
        ret = dict()
        max_node = max(beam.values(), key=lambda n: n.weight)
        for ngram, act_node in beam.items():
            if act_node.weight >= max_node.weight - self.log_theta:
                ret[ngram] = act_node
        return ret  # dict: {NGram -> Node}

    @staticmethod
    def update(beam: dict,  # {NGram -> Node}
               new_state: NGram,
               new_weight: float,
               from_node: Node):
        # Hozzá veszi, ha nincs benn ilyen végű(*) tag sorozat.
        # (*) Csak at utolsó két elemet veszi figyelembe az egyezésvizsgálatkor!
        if new_state not in beam.keys():
            beam[new_state] = Node(new_state, new_weight, from_node)
        # Ha már benne van, akkor módosítja a node-ot.
        elif beam[new_state].weight < new_weight:
            beam[new_state].prev = from_node
            beam[new_state].weight = new_weight
        else:
            pass
