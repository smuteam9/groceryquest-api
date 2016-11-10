from flask import Flask, request, jsonify, abort, g
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

import cgi
import json
import os

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///groceryquest'
app.config['DEBUG'] = True
db = SQLAlchemy(app)
CORS(app)
auth = HTTPBasicAuth()

from models import *

@app.route('/api/yo')
def yo():
    return "yo"


@app.route('/api/authtest')
@auth.login_required
def authtest():
    return "yo"


@auth.verify_password
def verify_password(username_or_token, password):
    # Attempt authentication with token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # Attempt authenticaiton with username and password
        user = User.query.filter_by(email=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/api/register', methods=['POST'])
def register_user():
    email = request.json.get('email')
    password = request.json.get('password')

    # Missing parameters
    if email is None or password is None:
        abort(400)

    # User exists
    if User.query.filter_by(email=email).first() is not None:
        abort(400)

    user = User(email=email)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()

    # TODO: Return token here
    return "user registered"


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    """
    """
    token = g.user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii') })


@app.route('/api/autocomplete/<text>')
def autocomplete(text):
    """Query database for autocompletions on list items."""

    products = Product.query.filter(
            Product.title.like('%{}%'.format(text))).all()

    results = []

    for p in products:
        results.append({"name" : p.title, "product_id" : p.upc})

    return json.dumps(results)


@app.route('/api/lists', methods=['POST'])
def get_lists():
    """
    Return lists belonging to a user.
    Expecting user_id param POST as json
    """

    #TODO: get user id from request
    current_user = User.query.filter_by(id=1).first()

    results = {}
    results['lists'] = [l.dict() for l in current_user.lists]

    return jsonify(**results)


@app.route('/api/list', methods=['POST'])
def get_list():
    """
    Return list by list_id
    Expecting user_id and list_id param POST as json
    """
    params = {k: str(v) for k, v in request.get_json().items()}

    grocery_list = List.query.filter_by(id=params['list_id'],
                                        user_id=params['user_id']).first()
    if grocery_list is None:
        abort(400)

    return jsonify(**grocery_list.dict())


@app.route('/api/addlist', methods=['POST'])
def add_list():
    """
    Create an empty list for a user, and return the new list's id
    Expects the following JSON params:

    title
    user_id
    store_id
    """
    params = {k: str(v) for k, v in request.get_json().items()}
    params = {k: cgi.escape(v) for k, v in params.items()}

    grocery_list = List(params['title'],
                        params['user_id'],
                        params['store_id'])

    db.session.add(grocery_list)
    db.session.commit()

    return jsonify(list_id=grocery_list.id)


@app.route('/api/updatelist', methods=['POST'])
def update_list():
    """
    Update a list by passing a whole new list
    to replace with.
    """
    params = request.get_json()

    grocery_list = List.query.filter_by(id=params['list_id']).first()

    if grocery_list is None:
        abort(400)

    # Update name
    grocery_list.title = params['title']

    # Update store
    grocery_list.store_id = params['store_id']

    # Delete all items in current list
    for item in grocery_list.items:
        db.session.delete(item)

    # Add new items
    for item in params['items']:
        product_id = item.get('product_id', None)
        product_id = cgi.escape(str(product_id)) if product_id else None

        position = cgi.escape(str(item.get('position')))

        name = item.get('name', None)
        name = cgi.escape(name) if name else None

        new_item = ListItem(product_id,
                            grocery_list.id,
                            position,
                            name)

        db.session.add(new_item)


    db.session.commit()

    return "list updated"


@app.route('/api/removelist', methods=['POST'])
def remove_list():
    """
    Remove user's list
    """
    params = {k: str(v) for k, v in request.get_json().items()}
    params = {k: cgi.escape(v) for k, v in params.items()}

    grocery_list = List.query.filter_by(id=params['list_id'],
                                        user_id=params['user_id']).first()

    db.session.delete(grocery_list)
    db.session.commit()

    return "list removed"


@app.route('/api/additem', methods=['POST'])
def add_item_to_list():
    """
    Add item to grocery list,
    expecting the following params from POST request in json:

    user_id
    list_id
    position
    product_id (optional)
    name
    """
    #TODO: get user id from request
    #TODO: assert parameters

    params = {k: str(v) for k, v in request.get_json().items()}
    params = {k: cgi.escape(v) for k, v in params.items()}

    grocery_list = List.query.filter_by(id=params['list_id'], user_id=1).first()

    product_id = params.get('product_id', None)

    item = ListItem(product_id, grocery_list.id,
                    params['position'], params['name'])

    db.session.add(item)
    db.session.commit()

    return "item added"


@app.route('/api/removeitem', methods=['POST'])
def remove_item_from_list():
    """
    Remove item from list,
    expecting the following params POST request in json:

    list_id
    item_id
    """
    params = {k: str(v) for k, v in request.get_json().items()}
    params = {k: cgi.escape(v) for k, v in params.items()}

    item = ListItem.query.filter_by(id=params['item_id'],
                                    list_id=params['list_id']).first()

    db.session.delete(item)
    db.session.commit()

    return "item removed"


if __name__ == '__main__':
    import logging
    logging.basicConfig(filename='error.log', level=logging.DEBUG)
    app.run(host='0.0.0.0')

