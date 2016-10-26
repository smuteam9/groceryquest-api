from app import app, db

from models import *


# Create a test user
test_user = User("user@test.lan", "password")
db.session.add(test_user)
db.session.commit()

# Create some products
cheetos = Product("cheetos", "100001")
lucky_charms = Product("lucky_charms", "100002")
db.session.add(cheetos)
db.session.add(lucky_charms)
db.session.commit()

# Create a store
kroger_mockingbird = Store("Kroger, Mockingbird Ln, Dallas, TX, 75206")
db.session.add(kroger_mockingbird)
db.session.commit()

# Create locations for products in store
cheetos_location = Location(cheetos.id, "3", kroger_mockingbird.id)
lucky_charms_location = Location(lucky_charms.id, "7", kroger_mockingbird.id)
db.session.add(cheetos_location)
db.session.add(lucky_charms_location)
db.session.commit()

# Create a list
grocery_list = List("my list", test_user.id, kroger_mockingbird.id)
db.session.add(grocery_list)
db.session.commit()

# Add some products to list
cheetos_list_item = ListItem(cheetos.id, grocery_list.id, 1)
lucky_charms_item = ListItem(cheetos.id, grocery_list.id, 2)
db.session.add(cheetos_list_item)
db.session.add(lucky_charms_item)
db.session.commit()
