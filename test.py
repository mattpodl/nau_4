import json

with open('ratings.json', 'r') as f:
    data = json.loads(f.read())

print(data)
