from datetime import datetime, timezone
from flask import render_template, request, redirect, Blueprint, url_for, flash

from .forms import ClusterSelectionForm

from ..build_feed import FeedDB, url_get_host
from ..tweet_db import TweetDB

main_blueprint = Blueprint("main", __name__, template_folder="templates")

# db = FeedDB("db/test_db2.json")

tweet_db = TweetDB("db/tweet_db_1-eth-python-bitcoin-external-quote-bank2.json")

CURRENT_CLUSTER = "Ethereum"


def borg_get_account_details(uid):
    url = f"https://api.borg.id/providers/accounts/twitter/{uid}/"


@main_blueprint.route("/", methods=["GET", "POST"])
def index():
    form = ClusterSelectionForm(request.form)
    if form.validate_on_submit():
        CURRENT_CLUSTER = form.data["cluster"]
    else:
        CURRENT_CLUSTER = "Ethereum"
    external_url_feed = tweet_db._db[CURRENT_CLUSTER]["external_url_feed"]
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


@main_blueprint.route("/get_shares/<ref_tweet_id>", methods=["GET"])
def get_shares(ref_tweet_id):
    print(ref_tweet_id)
    ref_tweet_obj = tweet_db._db[CURRENT_CLUSTER]["external_url_quote_tweet_bank"][
        ref_tweet_id
    ]
    return render_template(
        "shares.html",
        ref_tweet_id=ref_tweet_id,
        vote_tweets=ref_tweet_obj["vote_tweets"],
    )


@main_blueprint.route("/about/")
def about():
    return render_template("about.html")
