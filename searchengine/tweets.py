import csv
import tweepy

from config import *

def download_tweets():
    print("Download tweets")

    # authenticate to Twitter
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    # test authentication
    try:
        api.verify_credentials()
        print("\tAuthentication OK")
    except:
        print("\tError during authentication")
    
    # retrieve hashtags by tweets
    def hashtags(tweet):
        return list(filter(lambda token: token.startswith('#'), tweet.split()))

    # retrieve User mention by tweets
    def mentions(tweet):
        return list(filter(lambda token: token.startswith('@'), tweet.split()))

    # get tweets dataset
    def get_all_tweets(screen_name):
        # Twitter only allows access to a users most recent 3240 tweets with this method
        print(f"\tGetting {user} tweets")

        # initialize a list to hold all the tweepy Tweets
        alltweets = []

        # make initial request for most recent tweets (200 is the maximum allowed count)
        new_tweets = api.user_timeline(screen_name=screen_name, count=200, tweet_mode="extended", lang="en")

        # save most recent tweets
        alltweets.extend(new_tweets)

        # save the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1

        # keep grabbing tweets until there are no tweets left to grab
        while len(new_tweets) > 0:
            print(f"\t\tGetting tweets before {oldest}")

            # all subsiquent requests use the max_id param to prevent duplicates
            new_tweets = api.user_timeline(screen_name=screen_name, count=200, tweet_mode="extended", max_id=oldest, lang="en")

            # save most recent tweets
            alltweets.extend(new_tweets)

            # update the id of the oldest tweet less one
            oldest = alltweets[-1].id - 1

            print(f"\t\t...{len(alltweets)} tweets downloaded so far")

        # transform the tweepy tweets into a 2D array that will populate the csv
        outtweets = [[tweet.created_at, tweet.id, tweet.full_text, hashtags(tweet.full_text), mentions(tweet.full_text), tweet.source, tweet.user.screen_name, tweet.user.name, tweet.retweet_count, tweet.favorite_count] for tweet in alltweets]

        # write the csv
        with open(f'{dir + str(screen_name).lower()}_tweets.csv', 'w', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(['created_at', 'id', 'text', 'hashtags', 'mentions', 'source', 'user_screen_name', 'user_name', 'retweet_count', 'favorite_count'])
            writer.writerows(outtweets)

        pass

    for user in twitter_users:
        get_all_tweets(user)
