import unittest 
from flask import Flask
from flask_testing import TestCase
from redwood import app

class RedwoodTest(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        app.config['BOOKMARKS_FILENAME'] = 'tests/bookmarks/bookmarks.json'
        return app

    def test_index_page(self):
        response = self.client.get("/")
        self.assertStatus(response, status_code=200)
        self.assertTemplateUsed("index.html")

    def test_bookmarks_page(self):
        expected_bookmarks = [ {"category": "Python",
                                "bookmarks": [{"text": "Django", "url": "http://www.djangoproject.com"},
                                              {"text": "Flask",  "url": "http://flask.pocoo.org/"}]},
                               {"category": "Clojure",
                                "bookmarks": [{"text": "Clojure", "url": ""}]}]
        
        response = self.client.get("/bookmarks")
        self.assertStatus(response, status_code=200)
        self.assertTemplateUsed("bookmarks.html")
        self.assertContext('bookmarks', expected_bookmarks)

if __name__ == '__main__':
    unittest.main()
