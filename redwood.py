from flask import Flask, render_template, request, make_response
from flask import redirect, url_for, abort, send_file
from werkzeug import secure_filename
import settings
from storage import get_s3_files_from_result, get_s3_folders_from_result
from storage import read_s3_bucket_folder, read_s3_file, write_s3_file, read_s3_stream
from photos import get_thumbnail_s3_url, get_photo_s3_url, add_collection_thumbnail_url
from photos import add_collection_url, load_photo_collection_list, get_raw_photo_collection
from photos import create_image_dict, get_photo_collection
from util import load_json
from datetime import datetime
import time
import pytz
import jwt
import hashlib
from jwt import ExpiredSignatureError
from functools import wraps

from pprint import pprint

def create_app():
    app = Flask(__name__)
    app.config.from_object(settings.DefaultConfiguration)

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

@app.context_processor
def inject_user():
    """
    Inject the current user into the template context.
    """
    return {"user": get_current_user()}

@app.before_request
def require_https():
    """
    The require_https method is a before request method that checks that the request
    is being made using https.
    (Actually since we are using heroku it will check that the x-forwarded-proto header
    is set to https and not http.)
    """
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
    return render_template('index.html')


def load_bookmarks():
    """
    Loads the bookmarks from the bookmarks.json file
    """
    filename = app.config['BOOKMARKS_FILENAME']
    return load_json(filename)

def collect_bookmark_categories():
    """
    Create a list of bookmark categories from the bookmarks.
    """
    result = []
    for collection in load_bookmarks():
        slug = collection.get('slug', None)
        category = collection.get('category', None)

        assert slug is not None
        assert category is not None
   
        result.append({
            "category": category,
            "url": "/bookmarks/{}".format(slug)
        })

    return result

@app.route('/bookmarks')
def bookmarks():
    """
    Show the different bookmark categories.
    """
    bookmark_categories = collect_bookmark_categories()
    return render_template('bookmarks.html', categories=bookmark_categories)

def fetch_bookmark_collection_for_category(category):
    for collection in load_bookmarks():
        slug = collection.get('slug', None)

        if not slug:
            raise LookupError('Bookmark category missing slug.')

        if slug == category:
            return collection

    return None

@app.route('/bookmarks/<category_slug>')
def bookmark_category(category_slug):
    """
    Show the bookmarks for a given category.
    """
    bookmark_collection = fetch_bookmark_collection_for_category(category_slug)

    if bookmark_collection:
        category = bookmark_collection['category']
        bookmarks = bookmark_collection['bookmarks']
        return render_template('bookmark-category.html', category=category, bookmarks=bookmarks)
    else:
        abort(404)
    
@app.route('/photos')
def photo_collection_list():
    """
    Show list of photo collections.
    """
    filename = app.config['PHOTO_COLLECTION_FILENAME']
    photo_collections = load_photo_collection_list(filename)
    return render_template('photo-collection-list.html', photo_collections=photo_collections)


@app.route('/photos/<collection_name>')
def photo_collection(collection_name):
    """
    Show a single photo collection.
    """
    filename = app.config['PHOTO_COLLECTION_FILENAME']
    collection = get_photo_collection(collection_name, filename)

    if(collection):
        return render_template('photo-collection.html', collection=collection)
    else:
        return "Could not find the collection. Should return a nice 404 error here."

@app.route('/photos/<collection_name>/<photo>')
def single_photo(collection_name, photo):
    """
    Show a single photo from a photo collection.
    """
    filename = app.config['PHOTO_COLLECTION_FILENAME']
    collection = get_photo_collection(collection_name, filename)

    if collection:
        for image in collection['images']:
            if image['name'] == photo:
                return render_template("photo.html", image=image)
    
    return 'Could not find matching photo. Should return a nice 404 error here.'

@app.route('/time')
def current_time():
    """
    Show the current local time in different time zones.
    """
    places = [{"name": "Sweden:", "tz": "Europe/Stockholm"},
              {"name": "Hawaii:", "tz": "Pacific/Honolulu"},
              {"name": "California:", "tz": "America/Los_Angeles"},
              {"name": "Wyoming:", "tz": "US/Mountain"}]

    for place in places:
        place['time'] = datetime.now(pytz.timezone(place['tz'])).strftime("%H:%M")
    
    return render_template("time.html", places=places)

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
    The created JWT has the role 'token_creator'.
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
    return render_template("account.html")

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
    The created JWT does not have any roles.
    """
    user = get_current_user()

    # Check that the user has the role token_creator
    if not is_token_creator(user):
        abort(401)
    
    username = user['username']
    FIFTEEN_MINUTES = 15*60
    roles = []
    token_jwt = create_user_jwt(username, FIFTEEN_MINUTES, roles)

    return render_template("token.html", token=token_jwt)

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

    # If this is a folder
    if path.endswith('/'):
        folders, files = read_s3_bucket_folder('redwood-notes', path)

        folders = process_folders(folders)
        files = process_files(path, files)

        return render_template('notes-folder.html', folders=folders, files=files)
    else: # Otherwise this is a file
        text = read_s3_file('redwood-notes', path)
        
        return render_template('notes-file.html', text=text)

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

@app.route('/files', methods=['GET', 'POST'])
@login_required
def files():
    """
    Upload and download files.
    """
    bucket_name = 'redwood-files'
    
    if request.method == 'POST':
        f = request.files['file']
        if(f):
            write_s3_file(bucket_name, secure_filename(f.filename), f.read())
  	      
        return redirect(url_for('files'))
    else:
        _, file_list = read_s3_bucket_folder(bucket_name, '/')
        return render_template('file-list.html', file_list=file_list)

@app.route('/files/<filename>', methods=['GET', 'PUT'])
@login_required
def single_file(filename):
    """
    Upload or download a single file. The filename can not contain slash /
    characters.
    """
    bucket_name = 'redwood-files'

    if request.method == 'PUT':
        write_s3_file(bucket_name, secure_filename(filename), request.data)
        return redirect(url_for('files'))
    else:
        # Both wget and curl send the following Accept header.
        # Accept: */*
        # A web browser will return an Accept header that contains text/html
        # This allows us to return different pages for web browsers and curl/wget.
        # I'm not sure that I want to do this.

        file_stream = read_s3_stream(bucket_name, filename)
        return send_file(file_stream,
            mimetype=mimetype_from_extension(filename))


@app.route('/work')
def work():
    """
    Work related stuff.
    """
    return render_template('work.html')

@app.route('/contact')
def contact():
    """
    Contact page.
    """
    return render_template('contact.html')

def mimetype_from_extension(filename):
    """
    Given a filename returns the mime type. This is determined based on the extension.
    """
    extension = filename.split('.')[-1]
    extensionMap = {"txt": "text/plain",
                    "css": "text/css",
                    "html": "text/html",
                    "gif":  "image/gif",
                    "jpg":  "image/jpeg",
                    "jpeg": "image/jpeg",
                    "png": "image/png",
                    "zip": "application/zip"
    }

    return extensionMap.get(extension.lower(), "application/octet-stream")

@app.route('/public/<token>/<filename>')
def public_files(token, filename):
    bucket_name = 'redwood-files'
    expected_token = load_environment_variable('PUBLIC_FILE_TOKEN')
    filename = secure_filename(filename)

    if not expected_token:
        abort(500)

    if token == expected_token:
        file_stream = read_s3_stream(bucket_name, filename)
        return send_file(file_stream,
            mimetype=mimetype_from_extension(filename))
    else:
        raise abort(403)


