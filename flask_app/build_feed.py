### Twitter API Auth, loading creds and instantiating client
from cmath import inf
import os
from pathlib import Path
import requests
import json
import datetime
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv
import tweepy
from tweepy.errors import TooManyRequests

load_dotenv()

consumer_key = os.environ["TWITTER_API_KEY"]
consumer_secret = os.environ["TWITTER_API_KEY_SECRET"]

access_token = os.environ["TWITTER_ACCESS_TOKEN"]
access_token_secret = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]

## Twitter api v2 uses this client object instead
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
    bearer_token=os.environ["TWITTER_API_BEARER_TOKEN"],
)


### Borg define base_url and header (for auth)

BORG_HEADER = {"Authorization": f"Token {os.environ['BORG_API_KEY']}"}
BORG_BASE_URL = "https://api.borg.id"


def get_clusters():
    """
    Hit the Borg API to get a list of available clusters

    Returns a list of dictionaries of cluster data structured like
    {'active': True, 'created_at': '2020-12-01T11:19:54Z', 'id': '2300535630', 'name': 'Tesla', 'updated_at': '2021-12-20T09:55:19Z'}
    """
    res = requests.get(f"{BORG_BASE_URL}/influence/clusters/", headers=BORG_HEADER)
    return res.json()["clusters"]  # returns a list of dictionaries of clusters


clusters = get_clusters()
[i["name"] for i in clusters]


def get_cluster_influencers(
    cluster_name, sort_direction="desc", pages=[0], sort_by="rank"
):
    """
    Get a list of influencers from a specific cluster (must be one of the clusters returned by `get_clusters()`)

    sort_by (str): can be one of rank, score, score_change_week, followers, following
    influence_type str(): one of personal, organisation, all # TODO: not including this yet
    """
    influencers = []
    for i_page in pages:
        res = requests.get(
            f"{BORG_BASE_URL}/influence/clusters/{cluster_name}/influencers/?page={i_page}&sort_by={sort_by}&sort_direction={sort_direction}",
            headers=BORG_HEADER,
        )
        influencers.extend(res.json()["influencers"])
    return influencers


def get_influencer_tweets(influencers):
    usernames = []
    for influencer in influencers:
        usernames.append(influencer["social_account"]["social_account"]["screen_name"])
    all_tweets = []
    NOW = datetime.datetime.now()
    NOW_24h = datetime.timedelta(hours=24)
    START_TIME = (datetime.datetime.now() - NOW_24h).isoformat("T")[:-3] + "Z"
    for i_influencer in influencers:
        i_username = i_influencer["social_account"]["social_account"]["screen_name"]
        try:
            user = client.get_user(username=i_username)
        except TooManyRequests as err:
            print("hitting limit... breaking for now")
            print(err)
            break
        if user.data:
            try:
                user_tweets = client.get_users_tweets(
                    user.data.id,
                    tweet_fields=[
                        "public_metrics",
                        "created_at",
                        "author_id",
                        "referenced_tweets",
                    ],
                    start_time=START_TIME,
                )
            except TooManyRequests as err:
                print("hitting limit... breaking for now")
                print(err)
                break
        else:
            print(f"no data found for user '{i_username}'")
        i_influencer["last_tweet_pull"] = str(NOW)
        if user_tweets.data:
            i_influencer["tweets"] = [i.data for i in user_tweets.data]
            all_tweets.extend([i.data for i in user_tweets.data])
        else:
            i_influencer["tweets"] = []
    return influencers, all_tweets


def get_external_urls(tweet):
    """
    Extract external links from a tweet by doing a request.get (which will follow redirects) and finding the final url
    """
    urls = re.findall(
        "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        tweet.text,
    )
    external_links = []
    if urls:
        for url in urls:
            try:
                # opener = urllib.request.build_opener()
                # request = urllib.request.Request(url)
                # response = opener.open(request)
                # actual_url = response.geturl()
                res = requests.get(url)
                actual_url = res.url
                if "twitter" not in actual_url:
                    external_links.append(actual_url)
            except Exception as err:
                print(f"error with url {url}. Prrint exception below")
                print(err)
    return external_links


def filter_tweets_for_external_urls(tweets):
    """
    Find tweets that **quote a tweet with an external url**.
    Keep a list of the tweets that "voted" for them by quoting it


    returns:
        {
            i_ref_tweet.id: {
                external_urls: [], this is a list of url's (ideally 1) that the quotoed tweet links to
                vote_tweets: [] # this is a list of tweets that quoted the tweet with the url
            }
        }

    """
    quoted_tweet_bank = (
        {}
    )  # keys are tweet_id (this tweet is quoted), values are list of tweets by influencers that quoted the key tweet
    for i_tweet in tweets:
        if "referenced_tweets" in i_tweet:
            # "referenced tweets" include quoted tweets, find them by checking "type" of referenced tweet (other types are "replied_to" and "retweeted")
            for i_ref_tweet in i_tweet["referenced_tweets"]:
                if i_ref_tweet["type"] == "quoted":
                    external_urls = get_external_urls(
                        client.get_tweet(i_ref_tweet["id"]).data
                    )
                    if len(external_urls):
                        if i_ref_tweet["id"] not in quoted_tweet_bank:
                            quoted_tweet_bank[i_ref_tweet["id"]] = {
                                "external_urls": external_urls,
                                "vote_tweets": [],
                            }
                        quoted_tweet_bank[i_ref_tweet["id"]]["vote_tweets"].append(
                            i_tweet
                        )
    return quoted_tweet_bank


class FeedDB:
    """
    Json Structure:
    cluster_name:
        influencers (list)
        all_feed_tweets (list)
        external_url_feed (list)
        external_url_quoted_tweet_bank (dict)

    Plan is to make a bunch of accessors directly to the json strucutre.
    Don't access via python attributes for now
    """

    def __init__(self, db_fpath):
        self.db_fpath = db_fpath
        if os.path.isfile(db_fpath):
            with open(db_fpath, "r") as f:
                self._db = json.load(f)
        else:
            os.makedirs(Path(db_fpath).parent, exist_ok=True)
            self._db = {}

    def load(self, db_fpath):
        with open(db_fpath, "r") as f:
            db = json.load(f)

    def save(self):
        with open(self.db_fpath, "w") as f:
            json.dump(self._db, f)

    def get_cluster_tweets(self, cluster_name):
        return (
            self._db[cluster_name]["all_feed_tweets"],
            self._db[cluster_name]["influencers"],
        )

    def fetch_tweets(self, cluster_name, influencer_pages=range(1)):
        feed = Feed(cluster_name, influencer_pages=influencer_pages)
        feed.fetch_tweets()
        # feed.build_feed()
        self._db[cluster_name] = feed.dict()

    def build_external_url_feed(self, cluster_name):
        url_tweet_bank = filter_tweets_for_external_urls(
            self._db[cluster_name]["all_feed_tweets"]
        )

        self._db[cluster_name]["external_url_quote_tweet_bank"] = url_tweet_bank

        self.external_url_feed = []
        for num, (i_tweet, i_tweet_data) in enumerate(url_tweet_bank.items()):
            # Quick code to grab the html description of the site
            response = requests.get(i_tweet_data["external_urls"][0])
            soup = BeautifulSoup(response.text)
            metas = soup.find_all("meta")
            description = None
            for meta in metas:
                if "name" in meta.attrs and meta.attrs["name"] == "description":
                    description = meta.attrs["content"]

            self.external_url_feed.append({"description": description, "tweets": []})
            for i in i_tweet_data["vote_tweets"]:
                self.external_url_feed[-1]["tweets"].append(
                    {
                        "external_urls": i_tweet_data["external_urls"],
                        "tweet_link": f"https://twitter.com/username/status/{i['id']}",
                        "tweet_text": i["text"],
                    }
                )

        self._db[cluster_name]["external_url_feed"] = self.external_url_feed
        return self.external_url_feed


class Feed:
    def __init__(self, cluster_name, sort_direction="desc", influencer_pages=[0]):
        self.cluster_name = cluster_name
        self.sort_direction = sort_direction
        self.influencer_pages = influencer_pages

    def dict(self):
        return {
            "influencers": self.influencers,
            "cluster": self.cluster_name,
            "all_feed_tweets": self.all_feed_tweets,
            # "external_url_quoted_tweet_bank": self.external_url_quoted_tweet_bank,
        }

    def fetch_tweets(self):
        self.influencers = get_cluster_influencers(
            self.cluster_name, self.sort_direction, pages=self.influencer_pages
        )

        self.influencers, self.all_feed_tweets = get_influencer_tweets(self.influencers)
        return self.influencers, self.all_feed_tweets
