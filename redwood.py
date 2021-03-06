import os
import time
import pytz
import json
from dateutil.relativedelta import relativedelta

from flask import (
    Flask,
    render_template,
    request,
    make_response
)
from flask import redirect, url_for, abort, send_file
from flask import send_from_directory
from werkzeug import secure_filename
import settings
from storage import (
    get_s3_files_from_result,
    get_s3_folders_from_result
)
from storage import (
    read_s3_bucket_folder,
    read_s3_file,
    write_s3_file,
    read_s3_stream,
    delete_s3_file
)
from photos import (
    get_thumbnail_s3_url,
    get_photo_s3_url,
    add_collection_thumbnail_url
)
from photos import (
    add_collection_url,
    load_photo_collection_list,
    get_raw_photo_collection
)
from photos import (
    create_image_dict,
    get_photo_collection
)

from bookmarks import load_all_bookmarks
from bookmarks import load_bookmark_collections
from writings import load_writing

from util import load_json
from datetime import (
    date,
    datetime
)

import jwt
import hashlib
from jwt import ExpiredSignatureError
from functools import wraps

from markdown import markdown

from settings import load_environment_variable

def create_app():
    app = Flask(__name__)
    app.config.from_object(settings.DefaultConfiguration)

    return app


app = create_app()


@app.route('/favicon.png')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.png', mimetype='image/png')


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
    Gets the current user. Gets the JWT from the request and parses out
    the result. Returns None if the JWT has expired.
    """
    identity_jwt = get_jwt_from_request()

    if identity_jwt:
        try:
            secret = app.config['IDENTITY_JWT_SECRET']
            identity = jwt.decode(identity_jwt.encode('utf-8'),
                                  secret, algorithms=['HS256'])
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
    The require_https method is a before request method that checks that the
    request is being made using https.
    (On Heroku this is done by checking that the x-forwarded-proto header
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


def validate_bookmarks(bookmark_categories):
    """
    Validate a list of bookmark categories from the bookmarks.
    """
    errors = []
    for collection in bookmark_categories:
        slug = collection.get('slug', None)
        category = collection.get('category', None)
        visibility = collection.get('visibility', None)

        if category is None:
            errors.append("Missing category")

        if slug is None:
            if category is not None:
                errors.append("Missing slug for category {}".format(category))
            else:
                errors.append("Missing slug")

        if visibility is None:
            if category is not None:
                errors.append("Missing visibility for category {}".format(category))
            elif slug is not None:
                errors.append("Missing visibility for slug {}".format(slug))
            else:
                errors.append("Missing visibility")

    return errors


@app.route('/bookmarks')
def bookmarks():
    """
    Show the different bookmark categories.
    """
    user = get_current_user()
    bookmark_categories = load_all_bookmarks()

    if user is None:
        bookmark_categories = [c for c in bookmark_categories if c['visibility'] == 'public']

    return render_template('bookmarks.html', categories=bookmark_categories)


@app.route('/bookmarks/<collection_slug>')
def bookmark_category(collection_slug):
    """
    Show the bookmarks for a given category.
    """
    bookmark_collections = load_bookmark_collections()

    if not collection_slug in bookmark_collections:
        abort(404)

    collection = bookmark_collections[collection_slug]

    user = get_current_user()
    if user is None:
        if collection["visibility"] == "private":
            abort(404)

    return render_template('bookmark-category.html',
                           category=collection['category'],
                           bookmarks=collection['bookmarks'])

@app.route('/photos')
def photo_collection_list():
    """
    Show list of photo collections.
    """
    filename = app.config['PHOTO_COLLECTION_FILENAME']
    photo_collections = load_photo_collection_list(filename)
    return render_template('photo-collection-list.html',
                           photo_collections=photo_collections)


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
                  "url": "/notes/" + f}
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


@app.route('/files/delete/<filename>', methods=['GET', 'POST'])
def delete_file(filename):
    """
    Delete a single file. The filename can not contain / characters.
    """
    bucket_name = 'redwood-files'
    if request.method == 'POST':
        delete_s3_file(bucket_name, filename)

        return redirect(url_for('files'))
    else:
        return render_template('delete-file.html', filename=filename)


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


def render_markdown(title, markdown_filename):
    content = load_writing(markdown_filename)

    # Use the fenced_code markdown extension to get support for newlines
    # in code blocks.
    html = markdown(content, extensions=['markdown.extensions.fenced_code'])

    return render_template("content.html",
                           content=html,
                           title=title)


@app.route('/interesting-languages')
def interesting_languages():
    return render_markdown("Interesting Languages", "interesting-languages.md")


@app.route('/gpg')
def gpg():
    return render_markdown("GPG", "gpg.md")


@app.route('/ssh-keys')
def ssh_keys():
    return render_markdown("SSH keys", "ssh_keys.md")


@app.route('/learning')
def learning():
    return render_markdown("Learning", "learning.md")


@app.route('/psychology')
def psychology():
    return render_markdown("Psychology", "psychology.md")


@app.route('/game-development-programming-languages')
def game_development_programming_languages():
    return render_markdown("Game Development Programming Languages",
                           "game_development_programming_languages.md")


@app.route('/left')
def days_left():
    target_date = date(2020, 10, 1)
    now = datetime.now().date()
    duration = target_date - now
    days = duration.days

    if days == 0:
        message = "Target date is today"
    elif days > 0:
        delta = relativedelta(target_date, now)
        message = "{} months and {} days left".format(delta.months, delta.days)
    else:
        message = "Target date has already occurred"

    return render_template("days_left.html", message=message)


@app.route('/api/bookmarks')
def api_bookmarks():
    all_bookmarks, errors = load_all_bookmarks()

    if errors:
        return { "errors": ["There was an error parsing the bookmarks file"] }, 500

    filtered_bookmarks = [{"bookmarks": b["bookmarks"],
                         "category": b["category"],
                         "slug": b["slug"]} for b in all_bookmarks
                        if b['visibility'] == 'public']
    response = make_response(json.dumps(filtered_bookmarks, indent=4, sort_keys=True))
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/video')
def video():
    return render_template("video.html")


stored_text = ""


@app.route('/storage', methods=['GET', 'POST'])
def storage():
    global stored_text

    authorization = request.headers.get('Authorization')
    if authorization != "Bearer decafbad":
        return "Not Authorized", 403

    if request.method == 'POST':
        content_length = int(request.headers.get('Content-Length'))
        if content_length > 128:
            return "Text is too large", 400
        stored_text = request.get_data()
        print("type of stored_text: {type(stored_text)}")
        return ""
    else:
        return stored_text

@app.route('/empty', methods=['GET'])
def empty():
    return ('', 200)

@app.route('/nocontent', methods=['GET'])
def nocontent():
    return ('', 204)

# Soundscape
# <iframe width="560" height="315" src="https://www.youtube.com/embed/8myYyMg1fFE" frameborder="0"
# allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
