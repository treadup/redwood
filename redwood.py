from flask import Flask, render_template, request, make_response
from flask import redirect, url_for, abort
import json
from datetime import datetime
import time
import pytz
import jwt
import os
import hashlib
import boto3
from jwt import ExpiredSignatureError
from functools import wraps
from io import StringIO, BytesIO

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
    app.config['IDENTITY_JWT_SECRET'] = load_environment_variable('IDENTITY_JWT_SECRET')
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

def get_jwt_from_request():
    """
    Gets the JWT from the request. Looks for the JWT in a cookie called
    identity_jwt or in the Authorization header.
    """
    cookie_identity_jwt = request.cookies.get('identity_jwt')
    header_identity_jwt = request.headers.get('Authorization')

    if cookie_identity_jwt:
        return cookie_identity_jwt
    else:
        return header_identity_jwt

def get_current_user():
    """
    Gets the current user. Gets the JWT from the request and parses out the result.
    Returns None if the JWT has expired.
    """
    identity_jwt = get_jwt_from_request()

    if identity_jwt:
        try:
            secret = app.config['IDENTITY_JWT_SECRET']
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
    """
    Shows the index page.
    """
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

def get_thumbnail_s3_url(collection_name, image_name):
    """
    Creates the thumbnail url given the collection name and the image name.
    """
    f = 'https://s3.amazonaws.com/rainforestphotos/{}/thumbs/thumb_{}'
    return f.format(collection_name, image_name)

def get_photo_s3_url(collection_name, image_name):
    """
    Creates the image url given the collection name and the image name.
    """
    f = 'https://s3.amazonaws.com/rainforestphotos/{}/{}'
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
    
def load_photo_collection_list():
    """
    Loads the photo collection list from the photo collection json file.
    """
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
    """
    Loads the raw photo collection. Checks that a collection with the
    given collection name exists before trying to load the collection.
    """
    photo_collections = load_photo_collection_list()
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
    
def get_photo_collection(collection_name):
    """
    Gets the photo collection for the given name. If there is no photo collection
    for the given name return None.
    """
    collection = get_raw_photo_collection(collection_name)

    if collection:
        collection['images'] = [create_image_dict(collection_name, img) for img in collection['images']]
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
    """
    Show a single photo from a photo collection.
    """
    user = get_current_user()
    collection = get_photo_collection(collection_name)

    if collection:
        for image in collection['images']:
            if image['name'] == photo:
                return render_template("photo.html", image=image, user=user)
    
    return 'Could not find matching photo. Should return a nice 404 error here.'

@app.route('/.well-known/acme-challenge/<challenge>')
def letsencrypt_verification(challenge):
    """
    The LetsEncrypt subdomain verification endpoint.
    """
    if challenge != load_environment_variable('LETS_ENCRYPT_CHALLENGE', 'challenge'):
        return 'Not the correct challenge'
    
    return load_environment_variable('LETS_ENCRYPT_RESPONSE', 'response')

@app.route('/time')
def current_time():
    """
    Show the current local time in different time zones.
    """
    user = get_current_user()
    places = [{"name": "Sweden:", "tz": "Europe/Stockholm"},
              {"name": "Hawaii:", "tz": "Pacific/Honolulu"},
              {"name": "California:", "tz": "America/Los_Angeles"},
              {"name": "Wyoming:", "tz": "US/Mountain"}]

    for place in places:
        place['time'] = datetime.now(pytz.timezone(place['tz'])).strftime("%H:%M")
    
    return render_template("time.html", places=places, user=user)

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
    
def create_user_jwt(username, expiration_time_delta, roles):
    """
    Creates a JWT for the given username.
    The JWT contains an expiration date set JWT_EXPIRATION_TIMEDELTA seconds
    into the future.
    """
    secret = app.config['IDENTITY_JWT_SECRET']
    expires = int(time.time()) + expiration_time_delta
    identity = {'username': username,
                'exp': expires,
                'roles': roles}
    
    return jwt.encode(identity, secret, algorithm='HS256').decode('utf-8')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    """
    Login for the user. GET displays the login form. POST handles
    validation of the credentials and creation of the identity JWT
    cookie.
    """
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
            time_delta = app.config['JWT_EXPIRATION_TIMEDELTA']
            roles = ['token_creator']
            resp.set_cookie('identity_jwt', value=create_user_jwt(username, time_delta, roles))
            return resp
        else:
            return render_template("login.html",
                                   login_error_message="Incorrect username or password.",
                                   action_url=action_url)
    else:
        return render_template("login.html", action_url=action_url)

@app.route('/protocol/')
def protocol():
    """
    A page showing the protocol that was used to access the page.
    Uses the fact that Heroku adds the x-forwarded-proto header
    which contains http or https depending on which protocol was used.
    """
    header = request.headers.get('x-forwarded-proto')

    if header:
        return "Using protocol: {}".format(header)
    else:
        return "No protocol header."

@app.route('/logout/')
def logout():
    """
    Logs out the user by destroying the JWT cookie.
    """
    resp = make_response(redirect("/", code=303))
    resp.set_cookie('identity_jwt', '', expires=0)
    return resp
    
@app.route('/account')
def account():
    """
    Shows information about the currently logged in user.
    """
    user = get_current_user()
    return render_template("account.html", user=user)

def is_token_creator(user):
    """
    Check that the user has the role token_creator
    """
    roles = user['roles']
    return 'token_creator' in roles

@app.route('/token')
@login_required
def token():
    """
    Creates and shows a JWT token that is valid for 15 minutes.
    """
    user = get_current_user()

    # Check that the user has the role token_creator
    if not is_token_creator(user):
        abort(401)
    
    username = user['username']
    FIFTEEN_MINUTES = 15*60
    roles = []
    token_jwt = create_user_jwt(username, FIFTEEN_MINUTES, roles)

    return render_template("token.html", token=token_jwt, user=user)

def get_s3_folders_from_result(result):
    """
    Gets the folders from a s3 list_objects result.
    """

    if 'CommonPrefixes' in result:
        folders = result['CommonPrefixes']
    else:
        folders = []

    return [x['Prefix'] for x in folders]

def get_s3_files_from_result(result):
    """
    Gets the files from a s3 list_objects result.
    """
    if 'Contents' in result:
        files = result['Contents']
    else:
        files = []

    return [x['Key'] for x in files]

def read_s3_bucket_folder(bucket_name, folder):
    """
    Reads the contents of an s3 folder in a bucket.
    """
    client = boto3.client('s3')

    kwargs = {'Bucket': bucket_name, 'Delimiter':'/'}

    if(folder != '/'):
        kwargs['Prefix'] = folder
    
    result = client.list_objects(**kwargs)

    folders = get_s3_folders_from_result(result)
    files = get_s3_files_from_result(result)

    return folders, files

def read_s3_file(bucket_name, key):
    """
    Reads the contents of an S3 text file.
    """
    client = boto3.client('s3')

    result = client.get_object(Bucket=bucket_name, Key=key)

    if result['ResponseMetadata']['HTTPStatusCode'] != 200:
        pass

    return result['Body'].read().decode('utf-8')

def write_s3_file(bucket_name, key, content):
    """
    Writes text to an S3 text file.
    """
    client = boto3.client('s3')
    file_like_content = BytesIO(content)
    result = client.put_object(Bucket=bucket_name, Key=key, Body=file_like_content)

    # TODO: Some kind of error handling.

def process_folders(folders):
    """
    Given a list of folder names create a list of folder dicts
    where the dict contains the keys "text" and "url". The "text"
    key contains the relative folder name. The "url" contains the
    url for the folder.
    """
    result = []

    for f in folders:
        text = f[0:-1].split('/')[-1] + '/'
        folder = {"text": text,
                  "url": "/notes/" + f }
        result.append(folder)

    return result

def process_files(path, files):
    """
    Given a list of filenames creates a list of file dicts where the dict 
    contains the keys "text" and "url". The value for the "text" key is the
    filename. The value for the "url" key is the url of the file.
    """
    result = []

    for f in files:
        text = f.split('/')[-1]
        url = '/notes/' + f

        result.append({"text": text, "url": url})

    return result

@app.route('/notes')
@app.route('/notes/<path:path>')
@login_required
def notes(path='/'):
    """
    Shows markdown notes hosted on S3. The notes should be a protected resource.
    In other words they require authentication to access.
    """
    user = get_current_user()

    # If this is a folder
    if path.endswith('/'):
        folders, files = read_s3_bucket_folder('redwood-notes', path)

        folders = process_folders(folders)
        files = process_files(path, files)

        return render_template('notes-folder.html', folders=folders, files=files, user=user)
    else: # Otherwise this is a file
        text = read_s3_file('redwood-notes', path)
        
        return render_template('notes-file.html', text=text, user=user)

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
    """
    Upload and download files.
    """
    # Upload and download files.
    # Edit text files in some sort of editor.
    # Upload files using curl using http headers for authentication.
    return 'The part of the site where you can manage files goes here.'

@app.route('/files/<filename>', methods=['GET', 'PUT'])
@login_required
def single_file(filename):
    """
    Upload or download a single file. The filename can not contain slash /
    characters.
    """
    bucket_name = 'redwood-files'

    if request.method == 'PUT':
        # TODO: See if we can use request.stream instead. That way
        # we can avoid using BytesIO as well.
        write_s3_file(bucket_name, filename, request.data)
        return "Wrote {}".format(filename)
    else:
        # Both wget and curl send the following Accept header.
        # Accept: */*
        # A web browser will return an Accept header that contains text/html
        # This allows us to return different pages for web browsers and curl/wget.      
        file_content = read_s3_file(bucket_name, filename)
        return file_content

@app.route('/work')
def work():
    """
    Work related stuff.
    """
    user = get_current_user()
    return render_template('work.html', user=user)

@app.route('/contact')
def contact():
    """
    Contact page.
    """
    user = get_current_user()
    return render_template('contact.html', user=user)

