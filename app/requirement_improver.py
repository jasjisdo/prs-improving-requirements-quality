# -*- coding: utf-8 -*-

import json
import time

import spacy
from nltk.tokenize import sent_tokenize

from algorithms.compounds_nouns import check_compounds_nouns
from algorithms.lexical import check_lexical
from algorithms.nominals import check_nominals
from algorithms.pos_regexes import check_pos_regexes
from algorithms.regexes import check_regexes


class RequirementChecker:
    LEXICON_LOCATION = './res/lexicons'

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
                'func': check_pos_regexes,
                'lexicon': json.load(open(f'{self.LEXICON_LOCATION}/lex_posregexs.json', encoding='utf-8'))
            },
            'CompoundNouns': {
                'config_name': 'CompoundNouns',
                'func': check_compounds_nouns,
                'lexicon': json.load(open(f'{self.LEXICON_LOCATION}/lex_compounds.json', encoding='utf-8'))
            },
            'Nominalization': {
                'config_name': 'Nominalization',
                'func': check_nominals,
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

    def run_algorithms(self):
        req_time_start = 0.0
        # Find and save ambiguities
        ambiguities_found = {}
        # For each requirement sent
        for req_i, req in enumerate(self.reqs):
            # Logging
            if self.is_logging:
                req_time_start = time.time()
                print(f'\nReq {req_i + 1} of {len(self.reqs)}')

            # Put space aside for ambiguities found, even if none exist
            ambiguities_found[req.id] = []
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
                    amb_alg['func'](ambiguities_found, amb_alg['lexicon'], req, sentence, sentence_start_index, doc)

            # Logging
            if self.is_logging:
                print(f'Req Running Time: {time.time() - req_time_start:.2f} sec')

        return ambiguities_found

    def check_quality(self):
        total_time_start = 0.0
        # Logging
        if self.is_logging:
            total_time_start = time.time()

        ambs_found = self.run_algorithms()
        # Logging
        if self.is_logging:
            print(f'\nTotal Running Time: {time.time() - total_time_start:.2f} sec\n')

        return ambs_found
