# -*- coding: utf-8 -*-

import json
import re
import time

import spacy
from nltk.corpus import wordnet as wn
from nltk.tokenize import sent_tokenize

from algorithms.lexical import check_lexical
from algorithms.regexes import check_regexes
from utils.ambiguity import create_ambiguity_object

wn.ensure_loaded()


class RequirementChecker:
    LEXICON_LOCATION = './app/lexicons'

    def __init__(self, reqs, config=None, is_logging=False):
        self.reqs = reqs
        self.config = config if config else {}
        self.nlp = spacy.load('en')
        self.is_logging = is_logging
        self.amb_algs = {
            'Lexical': {
                'config_name': 'Lexical',
                'func': check_lexical,
                'lexicon': json.load(open(f'{self.LEXICON_LOCATION}/lex_lexical.json', encoding='utf-8'))
            },
            'RegularExpressions': {
                'config_name': 'RegularExpressions',
                'func': check_regexes,
                'lexicon': json.load(open(f'{self.LEXICON_LOCATION}/lex_regexes.json', encoding='utf-8'))
            },
            'POSRegularExpressions': {
                'config_name': 'POSRegularExpressions',
                'func': self._check_posregexs,
                'lexicon': json.load(open(f'{self.LEXICON_LOCATION}/lex_posregexs.json', encoding='utf-8'))
            },
            'CompoundNouns': {
                'config_name': 'CompoundNouns',
                'func': self._check_compounds,
                'lexicon': json.load(open(f'{self.LEXICON_LOCATION}/lex_compounds.json', encoding='utf-8'))
            },
            'Nominalization': {
                'config_name': 'Nominalization',
                'func': self._check_nominals,
                'lexicon': json.load(open(f'{self.LEXICON_LOCATION}/lex_nominals.json', encoding="utf-8"))
            }
        }
        self._apply_config()

    def _apply_config(self):
        # Curate algorithms based on the config, if it has been set
        if 'algorithms' in self.config:
            # Currently acceptable options for algorithms
            acceptable_amb_algs = {
                'Lexical', 'RegularExpressions', 'POSRegularExpressions', 'CompoundNouns', 'Nominalization'}
            # Remove all unknown options from user-specified configuration
            self.config['algorithms'] = list(acceptable_amb_algs.intersection(set(self.config['algorithms'])))
            # Find the algorithms the user did not select
            algs_to_remove = acceptable_amb_algs.difference(self.config['algorithms'])

            for alg_name in algs_to_remove:
                del self.amb_algs[alg_name]

    @staticmethod
    def _check_posregexs(ambs_found, lexicon, req, sentence, sentence_start_index, doc):
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
            regexp = re.compile(amb_obj['regexp'], flags=re.I | re.X)
            # Search for all regexps in requirement
            for match in re.finditer(regexp, req_truple_string):
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

    @staticmethod
    def _check_compounds(ambs_found, lexicon, req, sentence, sentence_start_index, doc):
        # Go over all phrases in lexicon
        for _, amb_obj in lexicon.items():
            for chunk in doc.noun_chunks:
                compound_list = [token for token in chunk if (token.dep_ == 'compound')
                                 or (token.tag_ in ('NN', 'NNS', 'NNP', 'NNPS') and token.dep_ in ('nmod', 'amod'))
                                 or (token.tag_ == 'VBG' and token.dep_ == 'nmod')
                                 or token == chunk.root]
                if len(compound_list) > 2:
                    new_text = ' '.join([t.text for t in compound_list])
                    new_indexes = [compound_list[0].idx, compound_list[-1].idx + len(compound_list[-1].text)]
                    ambs_found[req.id].append(create_ambiguity_object(
                        amb_obj,
                        text=new_text,
                        index_start=sentence_start_index + new_indexes[0],
                        index_end=sentence_start_index + new_indexes[1]
                    ))

    @staticmethod
    def _check_nominals(ambs_found, lexicon, req, sentence, sentence_start_index, doc):
        # Go over all phrases in lexicon
        for _, amb_obj in lexicon.items():

            # Generate a list of gerund nouminalizations that have pos VB
            nominalizations = [[t for t in token.subtree] for token in doc
                               if (token.text[-3:] in amb_obj['gerund']
                                   or token.text[-4:] in amb_obj['gerund_plural'])
                               and token.tag_ == 'VBG'
                               and token.dep_ not in ('root', 'aux', 'advmod', 'compound', 'acl')
                               and doc[token.i - 1].dep_ != 'aux'
                               and token.text.lower() not in amb_obj['rule_exceptions']]

            # Generate a list of nominalizations with pos NN based on suffixes
            nouns = [token for token in doc if (token.lemma_[-4:] in amb_obj['suffixes_len4']
                                                or token.lemma_[-3:] in amb_obj['suffixes_len3']
                                                or token.lemma_[-2:] in amb_obj['suffixes_len2'])
                     and token.tag_ in ('NN', 'NNS')
                     and wn.synsets(token.text)]
            # Filter list of nouns based on semantic hierarchy
            for token in nouns:
                # Generate and flatten the list of hypernyms for each noun
                hypernyms = list(
                    map(lambda x: x.name().split('.')[0],
                        sum(wn.synsets(token.text)[0].hypernym_paths(), [])))
                # Only consider nouns that express an event or a process
                if [l for l in hypernyms if l in ['event', 'process', 'act']] \
                        and token.text.lower() not in amb_obj['rule_exceptions']:
                    nominalizations.append([t for t in token.subtree])

            # Return all ambiguous nominalization sequences found
            for token_seq in nominalizations:
                if token_seq:
                    new_text = ' '.join([t.text for t in token_seq])
                    new_indexes = [token_seq[0].idx, token_seq[-1].idx + len(token_seq[-1].text)]
                    ambs_found[req.id].append(create_ambiguity_object(
                        amb_obj,
                        text=new_text,
                        index_start=sentence_start_index + new_indexes[0],
                        index_end=sentence_start_index + new_indexes[1]
                    ))

    def run_algs(self):

        # Find and save ambiguities
        ambs_found = {}
        # For each requirement sent
        for req_i, req in enumerate(self.reqs):

            # Logging
            if self.is_logging:
                req_time_start = time.time()
                print(f'\nReq {req_i + 1} of {len(self.reqs)}')

            # Put space aside for ambiguities found, even if none exist
            ambs_found[req.id] = []

            # Split the sentences so the NLP and regular expression algorithms work properly and quicker
            sentences = sent_tokenize(req.text)

            # For each sentence
            for sentence in sentences:

                # We need this variable to offset the indexes of our matches
                # NOTE: If req.text contains multiple identical sentences, this will not work. Currently, it is assumed that sentences are unique.
                sentence_start_index = req.text.find(sentence)

                # Convert requirement into nlp doc
                doc = self.nlp(sentence)

                # Loop through all algorithms to run, as requested by the user
                for _, amb_alg in self.amb_algs.items():
                    # Run the algorithm attached to the object
                    amb_alg['func'](ambs_found, amb_alg['lexicon'], req, sentence, sentence_start_index, doc)

            # Logging
            if self.is_logging:
                print(f'Req Running Time: {time.time() - req_time_start:.2f} sec')

        return ambs_found

    def check_quality(self):

        # Logging
        if self.is_logging:
            total_time_start = time.time()

        ambs_found = self.run_algs()

        # Logging
        if self.is_logging:
            print(f'\nTotal Running Time: {time.time() - total_time_start:.2f} sec\n')

        return ambs_found
