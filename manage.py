from flask.cli import FlaskGroup

from flask_app.app import create_app
from flask_app.build_feed import FeedDB


cli = FlaskGroup(create_app=create_app)


@cli.command()
def pull_test_db():
    db = FeedDB("db/test_db.json")
    db.fetch_tweets("Ethereum", influencer_pages=range(6))
    db.save()


if __name__ == "__main__":
    cli()
