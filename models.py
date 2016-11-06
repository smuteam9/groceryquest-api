# This file includes the models for each object mapped to a database table
from datetime import datetime

from app import db

# User
#TODO: implement Flask-login methods
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), unique=True)
    password = db.Column(db.String())
    registered_on = db.Column(db.DateTime)

    lists = db.relationship('List', backref='user')

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.registered_on = datetime.utcnow()

    def __repr__(self):
        return "email: {}".format(self.email)


# Grocery lists
class List(db.Model):
    __tablename__ = 'lists'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'))

    items = db.relationship('ListItem', backref='list')

    def __init__(self, title, user_id, store_id):
        self.title = title
        self.user_id = user_id
        self.store_id = store_id

    def __repr__(self):
        return '<id: {}, title: {}>'.format(self.id, self.title)

    def dict(self):
        """
        Return grocery list as dict
        """
        result = {}
        result['list_id'] = self.id
        result['store_id'] = self.store_id
        result['title'] = self.title
        result['store'] = Store.query.filter_by(id=self.store_id)\
                               .first().title
        result['items'] = [ self._item_details(item) for item in self.items ]
        return result

    def _item_details(self, item):
        """
        Return details of item as dictionary
        """
        product = Product.query.filter_by(id=item.product_id).first()
        location = Location.query.filter_by(product_id=item.product_id,
                                            store_id=self.store_id).first()
        result = {}
        result['item_id'] = item.id
        result['name'] = item.name or product.title
        result['location'] = location.aisle_num if location else None
        result['position'] = item.position
        result['product_id'] = item.product_id

        return result


# Item in list
class ListItem(db.Model):
    __tablename__ = 'listitems'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    list_id = db.Column(db.Integer, db.ForeignKey('lists.id'))
    position = db.Column(db.Integer)
    name = db.Column(db.String())

    def __init__(self, product_id, list_id, position, name):
        self.product_id = product_id
        self.list_id = list_id
        self.position = position
        self.name = name


# Product with UPC code
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    upc = db.Column(db.Integer, unique=True)

    def __init__(self, title, upc):
        self.title = title
        self.upc = upc

    def __repr__(self):
        return '<id: {}, title: {}>'.format(self.id, self.title)


class Store(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    # address, zip code, etc.

    def __init__(self, title):
        self.title = title

    def __repr__(self):
        return '<id: {}, title: {}>'.format(self.id, self.title)


# Location of item in store
class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)

    # Location of item in store "3"
    aisle_num = db.Column(db.Integer)

    product_id = db.Column(db.ForeignKey('products.id'))
    store_id = db.Column(db.ForeignKey('stores.id'))

    def __init__(self, product_id, aisle_num, store_id):
        self.product_id = product_id
        self.store_id = store_id
        self.aisle_num = aisle_num

    def __repr__(self):
        return '<id: {}>'.format(self.id)

