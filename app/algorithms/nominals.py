# -*- coding: utf-8 -*-

from nltk.corpus import wordnet as wn

from utils.ambiguity import create_ambiguity_object
from utils.token_utils import get_text_and_indexes

wn.ensure_loaded()


def check_nominals(ambs_found, lexicon, req, sentence, sentence_start_index, doc):
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
                new_text, new_indexes = get_text_and_indexes(token_seq)
                ambs_found[req.id].append(create_ambiguity_object(
                    amb_obj,
                    text=new_text,
                    index_start=sentence_start_index + new_indexes[0],
                    index_end=sentence_start_index + new_indexes[1]
                ))