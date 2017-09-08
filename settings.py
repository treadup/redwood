import os

def load_environment_variable(name, default=None):
    try:
        return os.environ[name]
    except KeyError:
        return default

def load_boolean_environment_variable(name, default):
    s = load_environment_variable(name, '')

    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        return default


class DefaultConfiguration:

    BOOKMARKS_FILENAME = 'data/bookmarks.json'
    PHOTO_COLLECTION_FILENAME = 'photos/photo_collections.json'
    IDENTITY_JWT_SECRET = load_environment_variable('IDENTITY_JWT_SECRET')
    TWELVE_HOURS = 12*60*60
    JWT_EXPIRATION_TIMEDELTA = TWELVE_HOURS

    USERNAME = load_environment_variable('USERNAME')

    # Use XKCD style pass phrase.
    # http://xkcd.com/936/
    PASSWORD_HASH = load_environment_variable('PASSWORD_HASH')

    # The password salt can be generated using the token_hex function in
    # the secrets module.
    # You can also generate salt using the following command.
    # cat /dev/urandom | head -c 1024 | sha256sum
    PASSWORD_SALT = load_environment_variable('PASSWORD_SALT')
    HTTPS_REQUIRED = load_boolean_environment_variable('HTTPS_REQUIRED', True)

    # The UPLOAD_FOLDER variable does not seem to be used.
    UPLOAD_FOLDER = '/tmp/upload' 
