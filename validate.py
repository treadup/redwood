import json
from pprint import pprint

def load_data():
    with open("data/bookmarks.json") as f:
        data = json.loads(f.read())
        return data

def validate_category(category):
    if not "category" in category:
        print('Category does not have key "category"')
        pprint(category)
        exit(1)

    if not category["category"]:
        print('Category "category" can not be false.')
        pprint(category)
        exit(1)

    if not "slug" in category:
        print('Category does not have key "slug"')
        pprint(category)
        exit(1)

    if not category["slug"]:
        print('Category "slug" can not be false')
        pprint(category)
        exit(1)

    if not "bookmarks" in category:
        print('Category does not have key "bookmarks"')
        pprint(category)
        exit(1)

    if not category["bookmarks"]:
        print('Category "bookmarks" can not be false')
        pprint(category)
        exit(1)

data = load_data()

if not isinstance(data, list):
    print("Root element is not a list.")
    exit(1)

for category in data:
    validate_category(category)

print("Validation succeeded.")
