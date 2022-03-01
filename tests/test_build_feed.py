from flask_app.build_feed import (
    filter_tweets_for_external_urls,
    get_clusters,
    get_cluster_influencers,
)
from flask_app.build_feed import FeedDB


def test_fetch_feed():
    db = FeedDB("db/test_db.json")
    assert "Ethereum" in db._db, "Did you fetch cluster?"
    assert (
        "all_feed_tweets" in db._db["Ethereum"]
    ), "Your db should have an all_feed_tweets key"

    tweets, influencers = db.get_cluster_tweets("Ethereum")
    assert len(tweets) > 0, "you found no tweets in db..."
    assert len(influencers) > 0, "you have no influencers"

    for i_influencer in influencers:
        assert "tweets" in i_influencer, "Your influencer block no longer has tweets"
        assert (
            "last_tweet_pull" in i_influencer
        ), "Your influencers must have a 'last_tweet_pull' key... not found"


def test_external_url_feed(db):
    """
    This test still requires hitting the api (althought we have saved data...)
    because it has to get the referenced tweet from the id.

    Using a preloaded external_url feed
    """
    external_url_feed = db.get_external_url_feed("Ethereum")
    for i in external_url_feed:
        assert (
            "description" in i
        ), "feed must include a description key, even if value is None"
        assert len(i["external_urls"]) > 0, "must be at least one external_url for each"
        for i_tweet in i["tweets"]:
            assert isinstance(
                i_tweet["tweet_link"], str
            ), "tweet_link must be a str"  # TODO: make this a valid url check
            assert isinstance(i_tweet["tweet_text"], str), "tweet text must be a str"


def test_get_clusters():
    should_be_available = [
        "Tesla",
        "Ethereum",
        "Solana",
        "Bitcoin",
        "React",
        "Polkadot",
        "Dogecoin",
        "Crypto",
        "Poker",
        "NFT",
        "Python",
    ]
    clusters = get_clusters()
    for i_cluster in [i["name"] for i in clusters]:
        assert (
            i_cluster in should_be_available
        ), f"cluster '{i_cluster}' returned from Hive, but not in your should_be_available list! Was there an update?"


def test_get_influencers():
    influencers = get_cluster_influencers(
        "Ethereum", pages=[0], sort_by="score", sort_direction="desc"
    )
    assert len(influencers) == 50
    assert isinstance(influencers[0], dict)
    assert "attention_score" in influencers[0]
