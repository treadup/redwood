from flask import Flask, render_template, request, make_response
from flask import redirect
import json
from datetime import datetime
import time
import pytz
import jwt
from jwt import ExpiredSignatureError

from pprint import pprint

def create_app():
    app = Flask(__name__)
    app.config['BOOKMARKS_FILENAME'] = 'bookmarks.json'
    app.config['PHOTO_COLLECTION_FILENAME'] = 'photos/photo_collections.json'
    app.config['MUSIC_FILENAME'] = 'data/music.json'
    app.config['IDENTITY_JWT_SECRET'] = 'EiGie9chaish7AifYaec9UoJieFee8shTiaw6jeeHuuw1d6iePfi9Mi6ph'
    TWELVE_HOURS = 12*60*60
    app.config['JWT_EXPIRATION_TIMEDELTA'] = TWELVE_HOURS
    return app

app = create_app()

def get_current_user():
    secret = app.config['IDENTITY_JWT_SECRET']
    identity_jwt = request.cookies.get('identity_jwt')

    if identity_jwt:
        try:
            identity = jwt.decode(identity_jwt.encode('utf-8'), secret, algorithms=['HS256'])
            return identity
        except ExpiredSignatureError as err:
            return None

    return None

@app.route('/')
def index():
    user = get_current_user()
    return render_template('index.html', user=user)

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
    user = get_current_user()
    bookmarks=load_bookmarks()
    return render_template('bookmarks.html', bookmarks=bookmarks, user=user)

# For now I might just want a single page of photos.
# In other words have a single collection page and then
# a detail page for each photo.

def get_thumbnail_s3_url(collection_name, image_name):
    f = 'http://s3.amazonaws.com/rainforestphotos/{}/thumbs/thumb_{}'
    return f.format(collection_name, image_name)

def get_photo_s3_url(collection_name, image_name):
    f = 'http://s3.amazonaws.com/rainforestphotos/{}/{}'
    return f.format(collection_name, image_name)

def add_collection_thumbnail_url(collection):
    collection['thumbnail'] = get_thumbnail_s3_url(collection['slug'], collection['image'])

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
    user = get_current_user()
    photo_collections = load_photo_collection_list()
    return render_template('photo-collection-list.html', photo_collections=photo_collections, user=user)

def get_raw_photo_collection(collection_name):
    photo_collections = load_photo_collection_list()
    for collection in photo_collections:
        if collection['slug'] == collection_name:
            filename = 'photos/{}'.format(collection['collection'])
            return load_json(filename)

    return None

def map_image(collection_name, image_name):
    return {"name": image_name,
            "s3url": get_photo_s3_url(collection_name, image_name),
            "thumbnail": get_thumbnail_s3_url(collection_name, image_name),
            "url": '/photos/{}/{}'.format(collection_name, image_name)}
    
def get_photo_collection(collection_name):
    collection = get_raw_photo_collection(collection_name)

    if collection:
        collection['images'] = [map_image(collection_name, img) for img in collection['images']]
        return collection
    else:
        return None

@app.route('/photos/<collection_name>')
def photo_collection(collection_name):
    """
    Show a single photo collection.
    """
    user = get_current_user()
    collection = get_photo_collection(collection_name)

    if(collection):
        return render_template('photo-collection.html', collection=collection, user=user)
    else:
        return "Could not find the collection. Should return a nice 404 error here."

@app.route('/photos/<collection_name>/<photo>')
def single_photo(collection_name, photo):
    user = get_current_user()
    collection = get_photo_collection(collection_name)

    if collection:
        for image in collection['images']:
            if image['name'] == photo:
                return render_template("photo.html", image=image, user=user)
    
    return 'Could not find matching photo. Should return a nice 404 error here.'

@app.route('/.well-known/acme-challenge/FiJYIF8cu88TYGIAaFbtC_74mTdJjbyDUAegb2z6ALg')
def letsencrypt_verification():
    return 'FiJYIF8cu88TYGIAaFbtC_74mTdJjbyDUAegb2z6ALg.do-Ea0EwowSq-4RD9j1t9cNV_0hjtZRC28xzYDjdCTk'

@app.route('/time')
def current_time():
    user = get_current_user()
    places = [{"name": "Sweden:", "tz": "Europe/Stockholm"},
              {"name": "Hawaii:", "tz": "Pacific/Honolulu"},
              {"name": "California:", "tz": "America/Los_Angeles"},
              {"name": "Wyoming", "tz": "US/Mountain"}]

    for place in places:
        place['time'] = datetime.now(pytz.timezone(place['tz'])).strftime("%H:%M")
    
    return render_template("time.html", places=places, user=user)

def load_music():
    """
    Loads the bookmarks from the bookmarks.json file
    """
    filename = app.config['MUSIC_FILENAME']
    return load_json(filename)

@app.route('/music')
def music():
    user = get_current_user()
    music_json = load_music()

    # Good search: https://www.youtube.com/results?search_query=celtic+music

    return render_template("music.html", music_urls=music_urls, user=user)

def valid_credentials(username, password):
    return username == 'henrik' and password == 'foo'

def create_user_jwt(username):
    secret = app.config['IDENTITY_JWT_SECRET']
    time_delta = app.config['JWT_EXPIRATION_TIMEDELTA']
    expires = int(time.time()) + time_delta
    identity = {'username': username,
                'exp': expires}
    
    return jwt.encode(identity, secret, algorithm='HS256').decode('utf-8')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    # TODO: Consider using a CSRF token.
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if not username:
            render_template("login.html", login_error_message="You need to specify a username.")

        if not password:
            render_template("login.html", login_error_message="You need to specify a password.")

        if valid_credentials(username, password):
            resp = make_response(redirect("/", code=303))
            # TODO: This cookie is insecure.
            # Create a cookie using JWT.
            # jwt = create_user_jwt(username)
            resp.set_cookie('identity_jwt', create_user_jwt(username))
            return resp
        else:
            render_template("login.html", login_error_message="Incorrect username or password.")
        # Set the cookie.
    else:
        return render_template("login.html")

@app.route('/protocol/')
def protocol():
    header = request.headers.get('x-forwarded-proto')

    if header:
        return "Using protocol: {}".format(header)
    else:
        return "No protocol header."

@app.route('/logout/')
def logout():
    resp = make_response(redirect("/", code=303))
    resp.set_cookie('identity_jwt', '', expires=0)
    return resp
    
@app.route('/account')
def account():
    user = get_current_user()
    return render_template("account.html", user=user)

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

@app.route('/library')
def library():
    """
    List of books I am interested in.
    """
    return 'Book list goes here.' 
