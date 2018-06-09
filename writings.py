import os

def load_writing(filename):
    with open(os.path.join("writing/", filename)) as f:
        return f.read()
