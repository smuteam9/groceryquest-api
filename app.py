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
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')

    # Missing parameters
    if email is None or password is None:
        abort(400)

    # User exists
    if User.query.filter_by(email=email).first() is not None:
        abort(400)

    user = User(email=email)
    user.hash_password(password)
    user.first_name = first_name
    user.last_name = last_name
    db.session.add(user)
    db.session.commit()

    token = user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii') })


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    """
    """
    token = g.user.generate_auth_token()

    # Create timestamp entry for heat map
    timestamp = LoginTimestamp(g.user.id)
    db.session.add(timestamp)
    db.session.commit()

    return jsonify({ 'token': token.decode('ascii') })


@app.route('/api/autocomplete/<text>')
def autocomplete(text):
    """
    Expects store_id as GET parameter
    Query database for autocompletions on list items.
    """
    store_id = request.args.get('store_id', '')

    if not store_id:
        abort(400)

    products = Product.query.filter(
            Product.title.like('%{}%'.format(text))).all()

    results = []

    for p in products:
        location = Location.query.filter_by(product_id=p.id,
                                            store_id=store_id).first()
        results.append({"name" : p.title,
                        "product_id" : p.upc,
                        "aisle_num" : location.aisle_num \
                                if location else None})

    return json.dumps(results)


@app.route('/api/lists', methods=['GET'])
@auth.login_required
def get_lists():
    """
    Return lists belonging to a user.
    Expecting user_id param POST as json

    and token in Authorization Header
    """

    results = {}
    results['lists'] = [l.dict() for l in g.user.lists]

    return jsonify(**results)


@app.route('/api/list', methods=['POST'])
@auth.login_required
def get_list():
    """
    Return list by list_id
    Expecting the following JSON params

    list_id

    and token in Authorization Header
    """
    params = {k: str(v) for k, v in request.get_json().items()}

    grocery_list = List.query.filter_by(id=params['list_id'],
                                        user_id=g.user.id).first()
    if grocery_list is None:
        abort(400)

    return jsonify(**grocery_list.dict())


@app.route('/api/addlist', methods=['POST'])
@auth.login_required
def add_list():
    """
    Create an empty list for a user, and return the new list's id
    Expects the following JSON params:

    title
    store_id

    and token in Authorization Header
    """
    params = {k: str(v) for k, v in request.get_json().items()}
    params = {k: cgi.escape(v) for k, v in params.items()}

    grocery_list = List(params['title'],
                        g.user.id,
                        params['store_id'])

    db.session.add(grocery_list)
    db.session.commit()

    return jsonify(list_id=grocery_list.id)


@app.route('/api/updatelist', methods=['POST'])
@auth.login_required
def update_list():
    """
    Update a list by passing a whole new list
    to replace with.
    """
    params = request.get_json()

    # List id missing
    if not params.get('list_id', None):
        abort(400)

    grocery_list = List.query.filter_by(id=params['list_id']).first()

    # Couldn't find grocery list
    if grocery_list is None:
        abort(400)

    # List doesn't belong to current user
    if grocery_list not in g.user.lists:
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
@auth.login_required
def remove_list():
    """
    Remove user's list
    """
    params = {k: str(v) for k, v in request.get_json().items()}
    params = {k: cgi.escape(v) for k, v in params.items()}

    grocery_list = List.query.filter_by(id=params['list_id'],
                                        user_id=g.user.id).first()

    db.session.delete(grocery_list)
    db.session.commit()

    return "list removed"


@app.route('/api/additem', methods=['POST'])
@auth.login_required
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
    #TODO: assert parameters

    params = {k: str(v) for k, v in request.get_json().items()}
    params = {k: cgi.escape(v) for k, v in params.items()}

    grocery_list = List.query.filter_by(id=params['list_id'],
                                        user_id=g.user.id).first()

    # Couldn't find grocery list
    if grocery_list is None:
        abort(400)

    product_id = params.get('product_id', None)

    item = ListItem(product_id, grocery_list.id,
                    params['position'], params['name'])

    db.session.add(item)
    db.session.commit()

    return "item added"


@app.route('/api/removeitem', methods=['POST'])
@auth.login_required
def remove_item_from_list():
    """
    Remove item from list,
    expecting the following params POST request in json:

    list_id
    item_id
    """
    params = {k: str(v) for k, v in request.get_json().items()}
    params = {k: cgi.escape(v) for k, v in params.items()}

    grocery_list = List.query.filter_by(id=params['list_id']).first()

    # Grocery list doesn't belong to current user
    if grocery_list not in g.user.lists:
        abort(400)

    item = ListItem.query.filter_by(id=params['item_id'],
                                    list_id=params['list_id']).first()

    db.session.delete(item)
    db.session.commit()

    return "item removed"


@app.route('/api/profile')
@auth.login_required
def get_profile():
    """
    Expects token and returns user profile
    info (first and last name)
    """
    result = {'first_name': g.user.first_name,
              'last_name': g.user.last_name,
              'email': g.user.email,
              'heatmap': g.user.get_last_login_days()}

    return jsonify(**result)


if __name__ == '__main__':
    import logging
    logging.basicConfig(filename='error.log', level=logging.DEBUG)
    app.run(host='0.0.0.0')

