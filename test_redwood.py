import unittest
from flask import Flask
from flask_testing import TestCase
from redwood import app, create_user_jwt
import hashlib
import jwt
import time
import json
from glob import glob

class RedwoodTest(TestCase):

    def configure_user(self, app):
        username = 'henrik'
        salt = '123456789'
        password = 'foo'
        m = hashlib.sha256()
        m.update(salt.encode('utf-8'))
        m.update(password.encode('utf-8'))
        password_hash = m.hexdigest()

        app.config['HTTPS_REQUIRED'] = False
        app.config['USERNAME'] = username
        app.config['PASSWORD_SALT'] = salt
        app.config['PASSWORD_HASH'] = password_hash
        app.config['IDENTITY_JWT_SECRET'] = 'some kind of secret'
        app.config['JWT_EXPIRATION_TIMEDELTA'] = 3600 # One hour

    def create_app(self):
        self.configure_user(app)
        app.config['TESTING'] = True
        return app

    def get_cookie_from_client(self, cookie_name, client):
        for cookie in client.cookie_jar:
            if cookie.name == cookie_name:
                return cookie

        return None

    def set_client_identity_jwt(self, username, expiration_time, roles):
        # Set the identity JWT
        identity_jwt = create_user_jwt(username, expiration_time, roles=roles)
        self.client.set_cookie('localhost', 'identity_jwt', identity_jwt)

        actual_jwt_cookie = self.get_cookie_from_client('identity_jwt', self.client)
        self.assertIsNotNone(actual_jwt_cookie,
                             msg='The identity_jwt cookie does not appear to have been set correctly.')

    def test_index_page(self):
        response = self.client.get("/")
        self.assertStatus(response, status_code=200)
        self.assertTemplateUsed("index.html")

    def test_get_login_page(self):
        response = self.client.get('/login/')
        self.assertStatus(response, status_code=200)
        self.assertTemplateUsed("login.html")
        self.assertContext('action_url', '/login/')

    def test_get_login_page_with_redirect(self):
        response = self.client.get('/login/?redirect=/foo')
        self.assertStatus(response, status_code=200)
        self.assertTemplateUsed("login.html")
        self.assertContext('action_url', '/login/?redirect=%2Ffoo')

    def test_post_login_without_username(self):
        payload = {'password': 'foo'}
        response = self.client.post('/login/', data=payload)
        self.assertStatus(response, status_code=200)
        self.assertTemplateUsed('login.html')
        self.assertContext('action_url', '/login/')
        self.assertContext('login_error_message', 'You need to specify a username.')

    def test_post_login_without_password(self):
        payload = {'username': 'foo'}
        response = self.client.post('/login/', data=payload)
        self.assertStatus(response, status_code=200)
        self.assertTemplateUsed('login.html')
        self.assertContext('action_url', '/login/')
        self.assertContext('login_error_message', 'You need to specify a password.')

    def test_post_login_with_incorrect_username(self):
        payload = {'username': 'someone', 'password': 'foo'}
        response = self.client.post('/login/', data=payload)
        self.assertStatus(response, status_code=200)
        self.assertTemplateUsed('login.html')
        self.assertContext('action_url', '/login/')
        self.assertContext('login_error_message', "Incorrect username or password.")

    def test_post_login_with_incorrect_password(self):
        payload = {'username': 'henrik', 'password': 'bar'}
        response = self.client.post('/login/', data=payload)
        self.assertStatus(response, status_code=200)
        self.assertTemplateUsed('login.html')
        self.assertContext('action_url', '/login/')
        self.assertContext('login_error_message', "Incorrect username or password.")

    def assert_post_successful_login(self, login_url, redirect_url):
        payload = {'username': 'henrik', 'password': 'foo'}
        response = self.client.post(login_url, data=payload)

        # Check that the redirect to the root page is being done.
        self.assert_redirects(response, redirect_url)

        # Check that the cookie is set.
        cookie = self.get_cookie_from_client('identity_jwt', self.client)

        self.assertIsNotNone(cookie)
        self.assertEqual('/', cookie.path)

        identity_jwt = cookie.value
        secret = 'some kind of secret'

        # The secret should come from the configuration.
        identity = jwt.decode(identity_jwt.encode('utf-8'), secret, algorithms=['HS256'])

        self.assertIsNotNone(identity)
        self.assertEqual('henrik', identity['username'])
        self.assertEqual(['token_creator'], identity['roles'])

        # Need to check the expiration claim in the JWT.
        actual_exp = identity['exp']
        current_time = int(time.time())
        expected_exp = current_time + 3600

        self.assertTrue(abs(actual_exp - expected_exp) < 2, msg="JWT expiration time is incorrect.")

    def test_post_successful_login(self):
        login_url = '/login/'
        redirect_url = '/'
        self.assert_post_successful_login(login_url, redirect_url)

    def test_post_successful_login_with_redirect(self):
        login_url = '/login/?redirect=/foo'
        redirect_url = '/foo'
        self.assert_post_successful_login(login_url, redirect_url)

    def test_logout(self):
        payload = {'username': 'henrik', 'password': 'foo'}
        response = self.client.post('/login/', data=payload)
        cookie = self.get_cookie_from_client('identity_jwt', self.client)
        self.assertIsNotNone(cookie, msg='No JWT cookie created.')

        response = self.client.get('/logout/')
        cookie = self.get_cookie_from_client('identity_jwt', self.client)
        self.assertIsNone(cookie, msg='JWT cookie still present.')

    def test_token_with_token_creator_role(self):
        # Set the identity JWT
        self.set_client_identity_jwt('henrik', 3600, ['token_creator'])

        # Get the response
        response = self.client.get('/token')

        self.assertStatus(response, status_code=200)
        self.assertTemplateUsed('token.html')

        # Check the token value
        actual_token = self.get_context_variable('token')
        self.assertIsNotNone(actual_token)

        secret = app.config['IDENTITY_JWT_SECRET']
        identity = jwt.decode(actual_token.encode('utf-8'), secret, algorithms=['HS256'])

        self.assertEqual('henrik', identity['username'])
        self.assertEqual([], identity['roles'])

        # Check that the expiration date is 15 minutes from now.
        actual_exp = identity['exp']
        current_time = int(time.time())
        FIFTEEN_MINUTES = 15*60
        expected_exp = current_time + FIFTEEN_MINUTES

        self.assertTrue(abs(actual_exp - expected_exp) <= 1, msg="Incorrect expiration time")

    def test_token_with_incorrect_role(self):
        # Set the identity JWT
        self.set_client_identity_jwt('henrik', 3600, [])

        # Get the response
        response = self.client.get('/token')

        self.assertStatus(response, status_code=401)

    def test_work(self):
        response = self.client.get('/work')
        self.assertStatus(response, status_code=200)
        self.assertTemplateUsed('work.html')

    def test_lint_bookmark_json_files(self):
        for filename in glob('bookmarks/*.json'):
            with open(filename, 'r') as f:
                try:
                    json.load(f)
                except json.decoder.JSONDecodeError:
                    assert False, "Invalid json file: {}".format(filename)

if __name__ == '__main__':
    unittest.main()
