# -*- coding: utf-8 -*-

import re as regex

from utils.ambiguity import create_ambiguity_object
from utils.sentence_utils import is_user_story


def check_lexical(ambs_found, lexicon, req, sentence, sentence_start_index, _):
    # For each phrase in the lexicon
    for algorithm_name, amb_obj in lexicon.items():
        # Go over all phrases in lexicon
        if is_user_story(sentence) and algorithm_name == "pronoun_us":
            # skip algorithm "pronoun_us" when user story is detected.
            continue
        find_ambiguities_through_lexicon(amb_obj, ambs_found, req, sentence, sentence_start_index)


def whole_phrase_regexp(phrase):
    # Handle spaces in strings
    phrase = phrase.replace(' ', '\s')
    try:
        return regex.compile(r'\b{0}\b'.format(phrase), flags=regex.I | regex.X)
    except regex.error:
        return regex.compile(r'\b\{0}\b'.format(phrase), flags=regex.I | regex.X)


def find_ambiguities_through_lexicon(amb_obj, ambs_found, req, sentence, sentence_start_index):
    for word_phrase in amb_obj['lexicon']:
        # Search for all word phrases in sentence
        for match in regex.finditer(whole_phrase_regexp(word_phrase), sentence):
            # Throws out all lexical errors from final result list
            ambs_found[req.id].append(create_ambiguity_object(
                amb_obj,
                text=match[0],
                index_start=sentence_start_index + match.start(),
                index_end=sentence_start_index + match.end()
            ))