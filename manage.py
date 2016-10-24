# This is a manager script to run tasks on the app
#
# Tasks:
#
# db init - initialize database
# db migrate - generate migrations
# db upgrade - update database with latest migration

import os
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from app import app, db

app.config.from_object(os.environ['APP_SETTINGS'])

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
