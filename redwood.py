from flask import Flask, render_template
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def load_bookmarks():
    """
    Loads the bookmarks from the bookmarks.json file
    """
    with open('bookmarks.json') as f:
        bookmarks_json = f.read()

    return json.loads(bookmarks_json)

@app.route('/bookmarks')
def bookmarks(bookmarks=load_bookmarks()): # Hack to only load the bookmarks file once.
    """
    Show bookmarks belonging to different categories
    """
    return render_template('bookmarks.html', bookmarks=bookmarks)

@app.route('/photos')
def photos():
    return render_template('photos.html')

@app.route('/photos/<slug>')
def photo_collection(slug):
    return 'Photos go here.'

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
