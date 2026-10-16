Problem:
Build a Flask REST API with CRUD endpoints (create, list, get an item).

Reference Solution:
```python
from flask import Flask, jsonify, request, abort

app = Flask(__name__)
items = {}        # in-memory storage: id -> item
next_id = 1


@app.get("/items")
def list_items():
    return jsonify(list(items.values()))


@app.post("/items")
def create_item():
    global next_id
    data = request.get_json(silent=True)

    if not data or "name" not in data:
        abort(400, description="'name' is required")

    item = {"id": next_id, "name": data["name"]}
    items[next_id] = item
    next_id += 1
    return jsonify(item), 201


@app.get("/items/<int:item_id>")
def get_item(item_id):
    if item_id not in items:
        abort(404, description="Item not found")
    return jsonify(items[item_id])


@app.errorhandler(400)
@app.errorhandler(404)
def handle_error(error):
    return jsonify(error=error.description), error.code


if __name__ == "__main__":
    app.run(debug=True)
```
