from flask import Flask, render_template, request, make_response
from flask import redirect, url_for
import json
from datetime import datetime
import time
import pytz
import jwt
import os
import hashlib
from jwt import ExpiredSignatureError
from functools import wraps

from pprint import pprint

def load_environment_variable(name, default=None):
    try:
        return os.environ[name]
    except KeyError:
        return default

def create_app():
    app = Flask(__name__)
    app.config['BOOKMARKS_FILENAME'] = 'data/bookmarks.json'
    app.config['PHOTO_COLLECTION_FILENAME'] = 'photos/photo_collections.json'
    app.config['MUSIC_FILENAME'] = 'data/music.json'
    app.config['IDENTITY_JWT_SECRET'] = 'EiGie9chaish7AifYaec9UoJieFee8shTiaw6jeeHuuw1d6iePfi9Mi6ph'
    TWELVE_HOURS = 12*60*60
    app.config['JWT_EXPIRATION_TIMEDELTA'] = TWELVE_HOURS

    app.config['USERNAME'] = load_environment_variable('USERNAME')

    # Use XKCD style pass phrase.
    # http://xkcd.com/936/
    app.config['PASSWORD_HASH'] = load_environment_variable('PASSWORD_HASH')

    # The password salt can be generated using the token_hex function in
    # the secrets module.
    # You can also generate salt using the following command.
    # cat /dev/urandom | head -c 1024 | sha256sum
    app.config['PASSWORD_SALT'] = load_environment_variable('PASSWORD_SALT')

    https_required = load_environment_variable('HTTPS_REQUIRED', default='True')
    app.config['HTTPS_REQUIRED'] = https_required.strip() != 'False'
    
    # TODO: Validate that all required app config variables were set.
    
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

@app.before_request
def require_https():
    """
    The require_https method is a before request method that checks that the request
    is being made using https.
    (Actually since we are using heroku it will check that the x-forwarded-proto header
    is set to https and not http.)
    The LetsEncrypt url is white listed and you can access this url using plain http.
    """
    # Always allow access to the LetsEncrypt verification endpoint without requiring
    # https access.
    if request.endpoint == 'letsencrypt_verification':
        return None

    # If we are not configured to require HTTPS then do nothing.
    if not app.config['HTTPS_REQUIRED']:
        return None

    # If we are already using HTTPS then do nothing.
    protocol_header = request.headers.get('x-forwarded-proto')
    if protocol_header == 'https':
        return None

    print("About to check HTTP method.")
    if request.method == 'POST':
        # Render an error page.
        return render_template("post-https-only.html")
    elif request.method == 'GET':
        # Redirect to the HTTPS version of the page.
        return redirect(request.url.replace("http://", "https://"), code=302)

    return None 

def login_required(f):
    """
    The login required decorator will redirect you to the login page if you are not
    currently logged in.
    """
    @wraps(f)
    def login_required_wrapper(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            current_url = request.url
            login_url = url_for('login', redirect=current_url)

            return redirect(login_url, code=302)

        return f(*args, **kwargs)
    
    return login_required_wrapper

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
    f = 'https://s3.amazonaws.com/rainforestphotos/{}/thumbs/thumb_{}'
    return f.format(collection_name, image_name)

def get_photo_s3_url(collection_name, image_name):
    f = 'https://s3.amazonaws.com/rainforestphotos/{}/{}'
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
              {"name": "Wyoming:", "tz": "US/Mountain"}]

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
    music_collections = load_music()

    # Good search: https://www.youtube.com/results?search_query=celtic+music

    return render_template("music.html", music_collections=music_collections, user=user)

def valid_credentials(username, password):
    """
    Validates the users login credentials.
    """
    if(username != app.config['USERNAME']):
        return False

    # Calculates the password hash using the sha256 algorithm.
    # Uses salt and the password to calculate the password hash.
    m = hashlib.sha256()
    salt = app.config['PASSWORD_SALT']
    m.update(salt.encode('utf-8'))
    m.update(password.encode('utf-8'))
    password_hash = m.hexdigest()

    return password_hash == app.config['PASSWORD_HASH']
    
def create_user_jwt(username):
    """
    Creates a JWT for the given username.
    The JWT contains an expiration date set JWT_EXPIRATION_TIMEDELTA seconds
    into the future.
    """
    secret = app.config['IDENTITY_JWT_SECRET']
    time_delta = app.config['JWT_EXPIRATION_TIMEDELTA']
    expires = int(time.time()) + time_delta
    identity = {'username': username,
                'exp': expires}
    
    return jwt.encode(identity, secret, algorithm='HS256').decode('utf-8')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    redirect_url = request.args.get('redirect', None)

    # Change empty redirect_url to None
    if not redirect_url:
        redirect_url = None
    
    if redirect_url:
        action_url = url_for('login', redirect=redirect_url)
    else:
        action_url = url_for('login')
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if not username:
            return render_template("login.html",
                                   login_error_message="You need to specify a username.",
                                   action_url=action_url)

        if not password:
            return render_template("login.html",
                                   login_error_message="You need to specify a password.",
                                   action_url=action_url)

        if valid_credentials(username, password):
            if not redirect_url:
                redirect_url = "/"

            # Should be a 303 status code but Flask Testing does not support this.
            resp = make_response(redirect(redirect_url, code=302))
            resp.set_cookie('identity_jwt', create_user_jwt(username))
            return resp
        else:
            return render_template("login.html",
                                   login_error_message="Incorrect username or password.",
                                   action_url=action_url)
    else:
        return render_template("login.html", action_url=action_url)

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
@login_required
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

@app.route('/books')
def library():
    """
    Something to do with books that I like.
    """
    # Computer Graphics Programming in OpenGL with Java
    return 'Book list goes here.' 

@app.route('/recepies')
def recepies():
    """
    List of recepies.
    """
    # This should be a protected resource since I don't really feel this needs
    # to be publically accessible.
    #
    # TODO: Would be good to have a translation of spices between English
    # and swedish.

    # TODO: Could also be a good idea to have a page where you can do conversions
    # between Swedish and American measurements.

    return 'List of recepies goes here.'

@app.route('/files')
def files():
    # Upload and download files.
    # Edit text files in some sort of editor.
    # Upload files using curl using http headers for authentication.
    return 'The part of the site where you can manage files goes here.'

