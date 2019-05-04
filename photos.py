from util import load_json

def get_thumbnail_s3_url(collection_name, image_name):
    """
    Creates the thumbnail url given the collection name and the image name.
    """
    f = 'https://rainforestphotos.s3.amazonaws.com/{}/thumbs/thumb_{}'
    return f.format(collection_name, image_name)

def get_photo_s3_url(collection_name, image_name):
    """
    Creates the image url given the collection name and the image name.
    """
    f = 'https://rainforestphotos.s3.amazonaws.com/{}/{}'
    return f.format(collection_name, image_name)

def add_collection_thumbnail_url(collection):
    """
    Adds the collection thumbnail url to the collection.
    """
    collection['thumbnail'] = get_thumbnail_s3_url(collection['slug'], collection['image'])

def add_collection_url(collection):
    """
    Adds the collection url to the collection.
    """
    collection['url'] = '/photos/{}'.format(collection['slug'])

def load_photo_collection_list(filename):
    """
    Loads the photo collection list from the photo collection json file.
    """
    photo_collections =  load_json(filename)

    for collection in photo_collections:
        add_collection_url(collection)
        add_collection_thumbnail_url(collection)

    return photo_collections

def get_raw_photo_collection(collection_name, filename):
    """
    Loads the raw photo collection. Checks that a collection with the
    given collection name exists before trying to load the collection.
    """
    photo_collections = load_photo_collection_list(filename)
    for collection in photo_collections:
        if collection['slug'] == collection_name:
            filename = 'photos/{}'.format(collection['collection'])
            return load_json(filename)

    return None

def create_image_dict(collection_name, image_name):
    """
    Creates an image dict given the collection name and the image name.
    """
    return {"name": image_name,
            "s3url": get_photo_s3_url(collection_name, image_name),
            "thumbnail": get_thumbnail_s3_url(collection_name, image_name),
            "url": '/photos/{}/{}'.format(collection_name, image_name)}

def get_photo_collection(collection_name, filename):
    """
    Gets the photo collection for the given name. If there is no photo collection
    for the given name return None.
    """
    collection = get_raw_photo_collection(collection_name, filename)

    if collection:
        collection['images'] = [create_image_dict(collection_name, img) for img in collection['images']]
        return collection
    else:
        return None
