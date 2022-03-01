"""
conftest from http://alexmic.net/flask-sqlalchemy-pytest/ which is a great post on keeping your tests fast and isolated
"""
import os
import pytest

from flask_app.app import create_app
from flask_app.build_feed import FeedDB

TESTDB = "test_app.db"
TESTDB_PATH = "db/{}".format(TESTDB)
TEST_DATABASE_URI = "sqlite:///" + TESTDB_PATH


# db.get_cluster_feed(cluster_name)
# db.get_cluster_tweets(cluster_name)
# db.get_cluster_influencers(cluster_name)


@pytest.fixture(scope="session")
def db():
    return FeedDB("db/test_db2.json")


@pytest.fixture(scope="session")
def app(request):
    """Session-wide test `Flask` application."""
    settings_override = {
        "TESTING": True
    }  # , "SQLALCHEMY_DATABASE_URI": TEST_DATABASE_URI}
    app = create_app(deploy_mode="Test", settings_override=settings_override)

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope="function")
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope="function")
def session(db, request):
    """Creates a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    db.session = session

    def teardown():
        transaction.rollback()
        connection.close()
        session.remove()

    request.addfinalizer(teardown)
    return session
