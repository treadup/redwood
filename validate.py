import json

with open("data/bookmarks.json") as f:
    data = json.loads(f.read())
    
print("Validation succeeded.")
