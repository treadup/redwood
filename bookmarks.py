from util import load_json

def load_all_bookmarks():
    return load_bookmarks("data/bookmarks.json")

def load_bookmarks(filename):
    """
    Loads the bookmarks from the bookmarks.json file
    """
    result = load_json(filename)

    for ordinal, collection in enumerate(result):
        collection['ordinal'] = ordinal
        collection['url'] = "/bookmarks/{}".format(collection['slug'])

    errors = []

    return result, errors

def load_bookmark_collections():
    collections = {}
    bookmark_collections_list, errors = load_all_bookmarks()

    if errors:
        return None, errors

    for collection in bookmark_collections_list:
        collections[collection['slug']] = collection

    return collections, None
