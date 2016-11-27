# This file includes the models for each object mapped to a database table
from datetime import datetime

from itsdangerous import (TimedJSONWebSignatureSerializer
                                  as Serializer,
                                     BadSignature,
                                     SignatureExpired)

from passlib.apps import custom_app_context as pwd_context

from app import db

SECRET_KEY = "changeme"

# User
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), unique=True)
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    password_hash = db.Column(db.String())
    registered_on = db.Column(db.DateTime)

    lists = db.relationship('List', backref='user', order_by='List.store_id')
    login_timestamps = db.relationship('LoginTimestamp', backref='user')

    def __init__(self, email, password=None):
        self.email = email
        self.password_hash = password
        self.registered_on = datetime.utcnow()


    def __repr__(self):
        return "email: {}".format(self.email)


    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)


    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)


    def get_last_login_days(self):
        """
        Get user's login timestamps, convert to
        delta of days since today
        """
        return list(set(map(
            lambda time: time.timestamp.timetuple().tm_yday,
            self.login_timestamps)))

    #################
    # Token methods #
    #################

    def generate_auth_token(self, expiration=86400):
        s = Serializer("changeme", expires_in=expiration)
        return s.dumps({ 'id': self.id })


    @staticmethod
    def verify_auth_token(token):
        s = Serializer(SECRET_KEY)
        try:
            data = s.loads(token)
	# Token expired
        except SignatureExpired:
            return None
	# Invalid token
        except BadSignature:
            return None
        except:
            return None
        user = User.query.get(data['id'])
        return user


# User login timestamps (for heat map)
class LoginTimestamp(db.Model):
    __tablename__ = "login_timestamps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime)

    def __init__(self, user_id):
        self.user_id = user_id
        self.timestamp = datetime.utcnow()


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
        price = ProductPrice.query.filter_by(product_id=item.product_id,
                                             store_id=self.store_id).first()
        result = {}
        result['item_id'] = item.id
        result['name'] = item.name or product.title
        result['location'] = location.aisle_num if location else None
        result['position'] = item.position
        result['product_id'] = item.product_id
        result['price'] = price.price if price else None

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

    def __init__(self, title, upc=None):
        self.title = title
        self.upc = upc

    def __repr__(self):
        return '<id: {}, title: {}>'.format(self.id, self.title)


class ProductPrice(db.Model):
    __tablename__ = 'productprices'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.ForeignKey('products.id'))
    store_id = db.Column(db.ForeignKey('stores.id'))
    price = db.Column(db.Float)

    def __init__(self, product_id, store_id, price):
        self.product_id = product_id
        self.store_id = store_id
        self.price = price

    def __repr__(self):
        return '<id: {}, product_id: {}, store_id: {}, price: {}'.format(
                self.id, self.product_id, self.store_id, self.price)


class Store(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    address = db.Column(db.String())
    hours = db.relationship('StoreHour', backref='store',
            order_by='StoreHour.hour')

    def __init__(self, title):
        self.title = title

    def __repr__(self):
        return '<id: {}, title: {}>'.format(self.id, self.title)

    def dict(self):
        return {'store_id': self.id,
                'store': self.title,
                'address': self.address,
                'busyness': list(map(lambda h: h.busyness, self.hours))}



# Busyness by hour for a store
class StoreHour(db.Model):
    __tablename__ = 'storehours'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'))
    hour = db.Column(db.Integer)
    busyness = db.Column(db.Integer)

    def __init__(self, store_id, hour, busyness):
        self.store_id = store_id
        self.hour = hour
        self.busyness = busyness

    def __repr__(self):
        return '<id: {}, store_id: {}, hour: {}, busyness: {}>'.format(
                self.id, self.store_id, self.hour, self.busyness)


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

