

def create_ambiguity_object(amb_obj, *, text, index_start, index_end):
    return {
        "title": amb_obj['title'],
        "description": amb_obj['description'],
        "language_construct": amb_obj['language_construct'],
        "text": text,
        "index_start": index_start,
        "index_end": index_end
    }