from flask import Flask, render_template
import json

def create_app():
    app = Flask(__name__)
    app.config['BOOKMARKS_FILENAME'] = 'bookmarks.json'
    return app

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')

def load_bookmarks():
    """
    Loads the bookmarks from the bookmarks.json file
    """
    filename = app.config['BOOKMARKS_FILENAME']
    with open(filename) as f:
        bookmarks_json = f.read()

    return json.loads(bookmarks_json)

@app.route('/bookmarks')
def bookmarks(bookmarks=load_bookmarks()): # Hack to only load the bookmarks file once.
    """
    Show bookmarks belonging to different categories
    """
    return render_template('bookmarks.html', bookmarks=bookmarks)

# For now I might just want a single page of photos.
# In other words have a single collection page and then
# a detail page for each photo.

@app.route('/photos')
def photos():
    """
    Show list of photo collections.
    """
    return render_template('photos.html')

@app.route('/photos/<collection>')
def photo_collection(collection):
    """
    Show a single photo collection.
    """
    return 'Photos go here.'

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
