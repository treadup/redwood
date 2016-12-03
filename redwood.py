from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bookmarks')
def bookmarks():

    pythonBookmarks = [('Django', 'http://www.djangoproject.com'),
                       ('Flask', ''),
                       ('Jinja2', ''),
                       ('Django Rest Framework', ''),
                       ('Fabric', '')]
                       
    clojureBookmarks = [('Clojure', ''),
                        ('Clojure Toolbox', '')]
    
    marks = [{'name':'Python', 'items': pythonBookmarks},
             {'name':'Clojure', 'items': clojureBookmarks}]

    return render_template('bookmarks.html', bookmarks=marks)
