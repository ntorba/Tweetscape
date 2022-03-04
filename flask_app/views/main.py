from datetime import datetime, timezone
import os
from flask import render_template, request, redirect, Blueprint, url_for, flash

from .forms import ClusterSelectionForm

from ..build_feed import FeedDB, url_get_host
from ..tweet_db import TweetDB

main_blueprint = Blueprint("main", __name__, template_folder="templates")

from dotenv import load_dotenv
import tweepy

load_dotenv()

consumer_key = os.environ["TWITTER_API_KEY"]
consumer_secret = os.environ["TWITTER_API_KEY_SECRET"]

access_token = os.environ["TWITTER_ACCESS_TOKEN"]
access_token_secret = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]

## Twitter api v2 uses this client object instead 
twitter_client=tweepy.Client(
    consumer_key=consumer_key, 
    consumer_secret=consumer_secret, 
    access_token=access_token, 
    access_token_secret=access_token_secret,
    bearer_token=os.environ["TWITTER_API_BEARER_TOKEN"]
)
# db = FeedDB("db/test_db2.json")

tweet_db = TweetDB("db/tweet_db_1-eth-python-bitcoin-external-quote-bank2.json")

CURRENT_CLUSTER = "Ethereum"


def borg_get_account_details(uid):
    url = f"https://api.borg.id/providers/accounts/twitter/{uid}/"


@main_blueprint.route("/", methods=["GET", "POST"])
def index():
    form = ClusterSelectionForm(request.form)
    current_cluster = form.data.get("cluster")
    if not current_cluster:
        current_cluster = "Ethereum"
    external_url_feed = tweet_db._db[current_cluster]["external_url_feed"]
    external_url_feed = sorted(
        external_url_feed, key=lambda x: len(x["tweets"]), reverse=True
    )
    for obj in external_url_feed:
        created_at = obj["ref_tweet"]["created_at"]
        created_at = "".join(created_at.split(".")[:-1]) + "+00:00"
        created_at = datetime.fromisoformat(created_at)
        now = datetime.now(timezone.utc)
        obj["hours_since_shared"] = (now - created_at).total_seconds() // 3600

    return render_template(
        "index.html",
        form=form,
        feed=external_url_feed,
        url_get_host=url_get_host,
        len=len,
    )


@main_blueprint.route("/shares2")
def shares2():
    return render_template("shares-2.html")


@main_blueprint.route(
    "/get_shares/<ref_tweet_id>/", defaults={"current_cluster": "Ethereum"}
)
@main_blueprint.route("/get_shares/<ref_tweet_id>/<current_cluster>", methods=["GET"])
def get_shares(ref_tweet_id, current_cluster):
    print(ref_tweet_id)

    ref_tweet_obj = tweet_db._db[current_cluster]["external_url_quote_tweet_bank"][
        ref_tweet_id
    ]
    return render_template(
        "shares.html",
        ref_tweet_id=ref_tweet_id,
        vote_tweets=ref_tweet_obj["vote_tweets"],
        twitter_client=twitter_client
    )


@main_blueprint.route("/about/")
def about():
    return render_template("about.html")
