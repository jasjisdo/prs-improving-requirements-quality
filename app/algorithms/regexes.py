# -*- coding: utf-8 -*-

import re as regex

from utils.ambiguity import create_ambiguity_object


def check_regexes(ambs_found, lexicon, req, sentence, sentence_start_index, _):
    # Go over all regular expressions in lexicon
    for _, amb_obj in lexicon.items():
        # Create Python regular expression object
        regexp = regex.compile(amb_obj['regexp'], flags=regex.I | regex.X)
        # Search for all regexps in requirement
        for match in regex.finditer(regexp, sentence):
            ambs_found[req.id].append(create_ambiguity_object(
                amb_obj,
                text=match[0],
                index_start=sentence_start_index + match.start(),
                index_end=sentence_start_index + match.end()
            ))
