from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import *

@app.route('/')
def hello():
    return "Hello World!"


@app.route('/autocomplete/<text>')
def autocomplete(text):
    """Query database for autocompletions on list items."""

    #TODO: use params here
    products = Product.query.filter(
            Product.title.like('%{}%'.format(text))).all()

    results = {}

    for p in products:
        results[p.title] = p.upc

    return jsonify(**results)





if __name__ == '__main__':
    app.run()

