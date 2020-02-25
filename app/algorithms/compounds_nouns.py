from utils.ambiguity import create_ambiguity_object


def check_compounds_nouns(ambs_found, lexicon, req, sentence, sentence_start_index, doc):
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