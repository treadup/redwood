import unittest 
from flask import Flask
from flask_testing import TestCase
from redwood import app

class RedwoodTest(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        return app

    def test_index_page(self):
        response = self.client.get("/")
        self.assertStatus(response, status_code=200)
        self.assertTemplateUsed("index.html")

if __name__ == '__main__':
    unittest.main()
