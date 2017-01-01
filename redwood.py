from flask import Flask, render_template
import json
from pprint import pprint

def create_app():
    app = Flask(__name__)
    app.config['BOOKMARKS_FILENAME'] = 'bookmarks.json'
    app.config['PHOTO_COLLECTION_FILENAME'] = 'photos/photo_collections.json'
    return app

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')

def load_json(filename):
    """
    Loads json from the file with the given filename.
    """
    with open(filename) as f:
        contents = f.read()

    return json.loads(contents)

def load_bookmarks():
    """
    Loads the bookmarks from the bookmarks.json file
    """
    filename = app.config['BOOKMARKS_FILENAME']
    return load_json(filename)

@app.route('/bookmarks')
def bookmarks():
    """
    Show bookmarks belonging to different categories
    """
    bookmarks=load_bookmarks()
    return render_template('bookmarks.html', bookmarks=bookmarks)

# For now I might just want a single page of photos.
# In other words have a single collection page and then
# a detail page for each photo.

def get_thumbnail_url(collection_name, image_name):
    f = 'http://s3.amazonaws.com/rainforestphotos/{}/thumbs/thumb_{}'
    return f.format(collection_name, image_name)

def get_photo_url(collection_name, image_name):
    f = 'http://s3.amazonaws.com/rainforestphotos/{}/{}'
    return f.format(collection_name, image_name)

def add_collection_thumbnail_url(collection):
    collection['thumbnail'] = get_thumbnail_url(collection['slug'], collection['image'])

def add_collection_url(collection):
    collection['url'] = '/photos/{}'.format(collection['slug'])
    
def load_photo_collection_list():
    filename = app.config['PHOTO_COLLECTION_FILENAME']
    photo_collections =  load_json(filename)

    for collection in photo_collections:
        add_collection_url(collection)
        add_collection_thumbnail_url(collection)

    return photo_collections
    
@app.route('/photos')
def photo_collection_list():
    """
    Show list of photo collections.
    """
    photo_collections = load_photo_collection_list()
    return render_template('photo-collection-list.html', photo_collections=photo_collections)

def get_raw_photo_collection(collection_name):
    photo_collections = load_photo_collection_list()
    for collection in photo_collections:
        if collection['slug'] == collection_name:
            filename = 'photos/{}'.format(collection['collection'])
            return load_json(filename)

    return None

def map_image(collection_name, image_name):
    return {"name": image_name,
            "url": get_photo_url(collection_name, image_name),
            "thumbnail": get_thumbnail_url(collection_name, image_name)}
    

def get_photo_collection(collection_name):
    collection = get_raw_photo_collection(collection_name)

    if collection:
        collection['images'] = [map_image(collection_name, img) for img in collection['images']]
        print("Collection contents")
        pprint(collection)
        return collection
    else:
        return None

@app.route('/photos/<collection_name>')
def photo_collection(collection_name):
    """
    Show a single photo collection.
    """
    collection = get_photo_collection(collection_name)

    print("Collection contents:")
    pprint(collection)

    if(collection):
        # Replace the images array with an array of objects with
        # the following properties.
        # name, url, thumbnail (which is a url)
        return render_template('photo-collection.html', collection=collection)
    else:
        return "Could not find the collection. Should return a nice 404 error here."

@app.route('/photos/<collection>/<photo>')
def single_photo(collection, photo):
    return 'Single photo goes here.'

# Have an index page for image collections.
# Each image collection should have a page 

@app.route('/notes')
@app.route('/notes/<path>')
def notes(path=None):
    """
    Shows markdown notes hosted on S3. The notes should be a protected resource.
    In other words they require authentication to access.
    """
    return 'Notes go here.'

@app.route('/hacks')
def hacks():
    """
    List of projects that I have created.
    """
    return 'Hacks go here.'
