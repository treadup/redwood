from util import load_json
import os.path

def load_all_bookmarks():
    filenames = [
        "python.json",
        "clojure.json",
        "go.json",
        "javascript.json",
        "lisp.json",
        "web.json",
        "editors.json",
        "bookmarks.json",
        "project_management.json",
        "commerce.json",
        "linux.json"]

    result = []

    for filename in filenames:
        result.extend(load_bookmarks(os.path.join("bookmarks", filename)))

    return result

def load_bookmarks(filename):
    """
    Loads the bookmarks from the bookmarks.json file
    """
    result = load_json(filename)

    for ordinal, collection in enumerate(result):
        collection['ordinal'] = ordinal
        collection['url'] = "/bookmarks/{}".format(collection['slug'])

    return result

def load_bookmark_collections():
    collections = {}
    bookmark_collections_list = load_all_bookmarks()

    for collection in bookmark_collections_list:
        collections[collection['slug']] = collection

    return collections
