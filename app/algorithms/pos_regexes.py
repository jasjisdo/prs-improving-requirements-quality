# -*- coding: utf-8 -*-

import re as regex

from utils.ambiguity import create_ambiguity_object


def check_pos_regexes(ambs_found, lexicon, req, sentence, sentence_start_index, doc):
    # Get the original indexes, before the truple design messed with it
    def get_original_indexes(req_original_string, req_tokenized_string, req_truple_string, match):
        # Add up extra letters (indexes) due to truple design
        def count_extra_indexes(up_to_index):
            # Count the extra letters in a given truple
            def count_extra_letters(req_truple):
                try:
                    split = req_truple.split('°')
                    return len(split[1]) + len(split[2]) + 2
                except:
                    return 0

            # Calculate space added by tokenization process
            def count_tokenize_space(req_original_string, req_tokenized_string):
                orig_i = 0
                tokn_i = 0
                while tokn_i < len(req_tokenized_string):
                    if req_original_string[orig_i] != req_tokenized_string[tokn_i]:
                        tokn_i += 1
                        continue
                    orig_i += 1
                    tokn_i += 1
                return tokn_i - orig_i

            # Remove string after the index
            words_pre_index = req_truple_string[:up_to_index].split()
            # Calculate extra indexes added by the truple system
            extra_truple_indexes = sum([count_extra_letters(req_truple) for req_truple in words_pre_index])
            # Update the 'up_to_index' to reflect the newly discovered mistakes
            up_to_index = up_to_index - extra_truple_indexes
            # Calculate the extra indexes added by the tokenizing process
            extra_tokenize_space = count_tokenize_space(req_original_string[:up_to_index],
                                                        req_tokenized_string[:up_to_index])

            return extra_truple_indexes + extra_tokenize_space

        return (
            match.start() - count_extra_indexes(match.start()),
            match.end() - count_extra_indexes(match.end()))

    # Create list of truples strings (word, POS tag, lemma) with degree symbol in between each part
    truple_list = ['{0}°{1}°{2}'.format(token.text, token.tag_, token.lemma_) for token in doc]

    # Create variables for easier and more readable use later
    req_original_string = sentence
    req_tokenized_string = ' '.join([token.text for token in doc])
    req_truple_string = ' '.join(truple_list)  # Convert into string so regex can be performed

    # Check against each regular expression in the lexicon
    for _, amb_obj in lexicon.items():
        # Create Python regular expression object
        regexp = regex.compile(amb_obj['regexp'], flags=regex.I | regex.X)
        # Search for all regexps in requirement
        for match in regex.finditer(regexp, req_truple_string):
            # Get the original indexes, since the truple string design messes with them
            orig_indexes = get_original_indexes(
                req_original_string, req_tokenized_string, req_truple_string, match)

            orig_text = ' '.join([req_truple.split('°')[0] for req_truple in match[0].split()])
            # Save this found ambiguity
            ambs_found[req.id].append(create_ambiguity_object(
                amb_obj,
                text=orig_text,
                index_start=sentence_start_index + orig_indexes[0],
                index_end=sentence_start_index + orig_indexes[1]
            ))