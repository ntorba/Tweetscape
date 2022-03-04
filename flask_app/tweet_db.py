import os
import json
import re
import requests
from time import sleep
import concurrent.futures
from tqdm import tqdm
from bs4 import BeautifulSoup
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


class TweetDB:
    """
    Json Structure:
    cluster_name:
        twitter_username: {
            "tweets": [chrono_order],
            "ids": {},
            "last_pull": str (datetime str)
        }
    """

    def __init__(self, db_fpath):
        self.db_fpath = db_fpath
        if os.path.isfile(db_fpath):
            with open(db_fpath, "r") as f:
                self._db = json.load(f)
        else:
            raise Exception("must read json file")

    def save(self, fpath):
        with open(fpath, "w") as f:
            json.dump(self._db, f)

    def get_cluster_tweets(self, cluster_name):
        return (
            self._db[cluster_name]["all_feed_tweets"],
            self._db[cluster_name]["influencers"],
        )

    def get_external_url_tweet_bank(self, cluster_name, start_time, update=False):
        if not update and "external_url_quote_tweet_bank" in self._db[cluster_name]:
            print("I am just returning this, not doing something dumb...")
            return self._db[cluster_name]["external_url_quote_tweet_bank"]
        # else:
        #     feed = self.get_feed(cluster_name, start_time)

        #     tweets_with_ref = []
        #     for i_tweet in feed:
        #         if "referenced_tweets" in i_tweet:
        #             for ref in i_tweet["referenced_tweets"]:
        #                 if ref["type"] == "quoted":
        #                     tweets_with_ref.append(i_tweet)

        #     build_quote_tweet_bank = input(
        #         f"going to pull data for {len(tweets_with_ref)} tweets. is that okay? [y,n]"
        #     )

        #     if build_quote_tweet_bank == "y":
        #         url_tweet_bank = filter_tweets_for_external_urls(tweets_with_ref)
        #     else:
        #         url_tweet_bank = None

        #     return url_tweet_bank

    def build_external_url_feed(self, cluster_name, start_time):
        url_tweet_bank = self.get_external_url_tweet_bank(cluster_name, start_time)
        self._db[cluster_name]["external_url_quote_tweet_bank"] = url_tweet_bank

        self.external_url_feed = []
        for num, (i_tweet, i_tweet_data) in enumerate(url_tweet_bank.items()):
            # Quick code to grab the html description of the site
            response = requests.get(
                i_tweet_data["external_urls"][0], headers={"User-Agent": "XY"}
            )
            soup = BeautifulSoup(response.text)
            description = (  # taken from https://stackoverflow.com/questions/22318095/get-meta-description-from-external-website/22318311
                soup.find("meta", attrs={"name": "description"})
                or soup.find("meta", attrs={"property": "description"})
                or soup.find("meta", attrs={"property": "og:description"})
                or soup.find("meta", attrs={"name": "description"})
            )
            if description:
                description = description.attrs["content"]
            title = soup.find("title")
            if title:
                title = title.text
            self.external_url_feed.append(
                {
                    "title": title,
                    "description": description,
                    "ref_tweet": i_tweet_data["ref_tweet_data"],
                    "external_urls": i_tweet_data["external_urls"],
                    "tweets": [],
                }
            )
            for i in i_tweet_data["vote_tweets"]:
                i["tweet_link"] = f"https://twitter.com/username/status/{i['id']}"
                self.external_url_feed[-1]["tweets"].append(i)

        self._db[cluster_name]["external_url_feed"] = self.external_url_feed
        return self.external_url_feed

    def get_feed(self, cluster_name, start_time):
        feed_tweets = []
        for num, (i_user_name, i_user_data) in enumerate(
            self._db[cluster_name].items()
        ):
            if (
                i_user_name == "external_url_quote_tweet_bank"
                or i_user_name == "external_url_feed"
            ):
                break
            add_tweets = True
            cur_index = 0
            while cur_index < len(i_user_data["tweets"]) and add_tweets:
                i_tweet = i_user_data["tweets"][cur_index]
                if i_tweet["created_at"] > start_time:
                    feed_tweets.append(i_tweet)
                else:
                    add_tweets = False
                cur_index += 1
        return feed_tweets


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

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(
            tqdm(executor.map(check_quote_get_url, tweets), total=len(tweets))
        )

    for urls, ref_tweet_data, vote_tweet_data in results:
        if urls:
            if ref_tweet_data["id"] not in quoted_tweet_bank:
                quoted_tweet_bank[ref_tweet_data["id"]] = {
                    "external_urls": urls,
                    "ref_tweet_data": ref_tweet_data,
                    "vote_tweets": [vote_tweet_data],
                }
            else:
                quoted_tweet_bank[ref_tweet_data["id"]]["vote_tweets"].append(
                    vote_tweet_data
                )
    return quoted_tweet_bank


def check_quote_get_url(vote_tweet):
    """
    If tweet quotes another tweet and that tweet has an external url, return the url, the quoted_tweet_id and the vote_tweet object, else return all Nones

    vote_tweet (dict): the data obj of tweepy.Tweet obj
        this becomes a true "vote tweet" if it qutoes another tweet that has an external url in it

    returns:
        external_urls: a list of the urls that are in the quoted/referenced tweet
        i_ref_tweet_data: the data object of the reference twet
        vote_tweet: the data object of the original tweet
    """

    if "referenced_tweets" in vote_tweet:
        # "referenced tweets" include quoted tweets, find them by checking "type" of referenced tweet (other types are "replied_to" and "retweeted")
        for i_ref_tweet in vote_tweet["referenced_tweets"]:
            if i_ref_tweet["type"] == "quoted":
                retry = True
                while retry:
                    try:
                        i_ref_tweet = client.get_tweet(
                            i_ref_tweet["id"],
                            tweet_fields=[
                                "public_metrics",
                                "created_at",
                                "author_id",
                                "referenced_tweets",
                            ],
                        )
                    except TooManyRequests as err:
                        print(
                            f"hitting api rate limit, sleeping for 1 minute, then continuing"
                        )
                        sleep(60)
                    else:
                        retry = False
                if i_ref_tweet.data and i_ref_tweet.data.data:
                    i_ref_tweet_data = (
                        i_ref_tweet.data.data
                    )  # TODO: add a check for failure to retrieve tweet...
                else:
                    return None, None, None
                external_urls = get_external_urls(i_ref_tweet_data)
                if external_urls:
                    return external_urls, i_ref_tweet_data, vote_tweet
                else:
                    return None, None, None
            else:
                return None, None, None

    else:
        return None, None, None


def get_external_urls(tweet):
    """
    Extract external links from a tweet by doing a request.get (which will follow redirects) and finding the final url
    """
    urls = re.findall(
        "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        tweet["text"],
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
                print(f"error with url {url}. Print exception below")
                print(err)
    return external_links
