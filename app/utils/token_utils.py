# -*- coding: utf-8 -*-


def get_text_and_indexes(token_seq):
    new_text = ' '.join([t.text for t in token_seq])
    new_indexes = [token_seq[0].idx, token_seq[-1].idx + len(token_seq[-1].text)]
    return new_text, new_indexes
