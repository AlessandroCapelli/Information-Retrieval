from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import re
import math
import string
import ast
from scipy import sparse
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

from config import *

def vectorize_texts():
    print("vectorize tweets and user keywords text")

    df = {}  # dict that will contain the original dataframe of each user
    list = {}  # dict that will contain the whole tweets text for each user

    for user in users:
        df[user+"_originale"] = pd.read_csv(dir + user + "_tweets.csv")

    for user in users:
        list[user] = df[user+"_originale"]['text'].replace(r'http\S+', '', regex=True).replace(r'www\S+', '', regex=True).tolist()

    list["all_tweets"] = list['@joebiden'] + list['@barackobama'] + list['@kamalaharris'] + list['@justinbieber'] + list['@jbalvin'] + list['@diplo']

    # extract keywords by tweets text for each user --> user profile = relevant words
    keywords = {}
    for user in users:
        # split text in tokens
        words = re.split(r'\W+', str(list[user]))
        # convert to lower case
        words = [w.lower() for w in words]
        # remove punctuation from each word
        table = str.maketrans('', '', string.punctuation)
        stripped = [w.translate(table) for w in words]
        # remove remaining tokens that are not alphabetic
        words = [word for word in stripped if word.isalpha()]
        # filter out stop words in english and spanish
        stop_words_english = set(stopwords.words('english'))
        stop_words_english.add("n")
        stop_words_english.add("u")
        stop_words_english.add("r")
        stop_words_english.add("rt")
        stop_words_spanish = set(stopwords.words('spanish'))

        words = [w for w in words if not w in stop_words_english]
        words = [w for w in words if not w in stop_words_spanish]

        # create keywords list for each user
        keywords["keywords_"+user] = ""
        for w in words:
            keywords["keywords_"+user] += w
            keywords["keywords_"+user] += " "

    # preprocessing all tweets with the same steps as user keywords
    keywords["keywords_all_tweets"] = keywords['keywords_@joebiden'] + keywords['keywords_@barackobama'] + keywords['keywords_@kamalaharris'] + keywords['keywords_@justinbieber'] + keywords['keywords_@jbalvin'] + keywords['keywords_@diplo']

    # control keywords list and list length
    #keywords["keywords_@diplo"]
    #len(keywords["keywords_@diplo"])

    '''
    # in case we just wanted top k relevant words
    from collections import Counter
    c = Counter(words)
    c.most_common(10)
    '''

    # create vector representation of keywords and text --> used for personalization
    # create TfidfVectorizer object
    tfidf = TfidfVectorizer(encoding='utf-8', max_features=1024)
    # fit with all users tweets text --> create vocabolary for all tweets
    tfidf_all_tweets_vect = tfidf.fit([keywords["keywords_all_tweets"]])

    # create keywords vector representation for each user --> shape 1x1024
    keywords_vec = {}
    for user in users:
        keywords_vec["keywords_"+user+"_vec"] = tfidf_all_tweets_vect.transform([keywords["keywords_"+user]])

    # save keywords vector representation for each user
    for user in users:
        sparse.save_npz("keywords_"+user+"_vec.npz", keywords_vec["keywords_"+user+"_vec"])

    # test load keywords sparse vector
    #load_sparse_matrix = sparse.load_npz("keyword_obama_vect.npz")

    # delete 'text_vector' dataframe column if already exist
    #for user in users:
    #   del df[user+"_originale"]["text_vector"] # oppure del df[@diplo_originale"]["text_vector"]

    # add the new text vector representation as a new dataframe column named 'text_vector' for each user
    user_vec = {}
    for user in users:
        user_vec[user+"_vec"] = tfidf_all_tweets_vect.transform(list[user]).toarray().tolist()
        df[user+"_originale"]["text_vector"] = user_vec[user+"_vec"]

    # delete tweets with 0 keywords --> give NAN result in cosine similarity
    for user in users:
        del_id = []
        for i in range(0, len(df[user+"_originale"])-1):
            if math.fsum(df[user+"_originale"]["text_vector"][i]) == 0:
                del_id.append(i)
        df[user+"_originale"] = df[user+"_originale"].drop(df[user+"_originale"].index[del_id])

    # save the new dataframe for each user
    for user in users:
        df[user+"_originale"].to_csv(dir + user + "_tweets.csv", index=False)
