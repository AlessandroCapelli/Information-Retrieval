import warnings
warnings.filterwarnings("ignore")
from config import *
from tweets import *
from text_vectorization import *

from elasticsearch import Elasticsearch
from textblob import TextBlob

es = Elasticsearch('http://elasticsearch_1', port=9200)

def create_index():
    print("Create index")

    client_body = {
        "settings": {
			"number_of_shards": 5, 
			"number_of_replicas": 2,
			"analysis": {
                "normalizer": {
                    "my_normalizer": {
                    "type": "custom",
                     "filter": ["lowercase", "asciifolding"]
                    }
                },
				"analyzer": {
					"my_analyzer": {
					    "type": "custom",
					    "tokenizer": "standard",
					    "filter": ["lowercase"]
					},
					"my_stop_analyzer": { 
					    "type": "custom",
					    "tokenizer": "standard",
					    "filter": [
						    "lowercase",
                            "english_synonym",
                            "english_stop"
						    #"porter_stem"
                        ]
					}
				},
                "filter": {
					"english_stop": {
					    "type": "stop",
					    "stopwords": "_english_"
					},
                    "english_synonym": {
                        "type": "synonym",
                        "synonyms_path": "analysis/synonyms.txt"
                    }
				}
			}
		},
		"mappings": {
            "properties": {
                "created_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss", "index": "false", "ignore_malformed": "true"},
                "id": {"type": "keyword", "index": "false"},
                "text": {"type": "text", "similarity": "BM25", "analyzer": "my_stop_analyzer", "search_analyzer": "my_stop_analyzer", "search_quote_analyzer": "my_analyzer"},
                "hashtags": {"type": "text", "similarity": "BM25", "analyzer": "my_stop_analyzer", "search_analyzer": "my_stop_analyzer", "search_quote_analyzer": "my_analyzer"},
                "mentions": {"type": "text", "similarity": "BM25", "analyzer": "my_stop_analyzer", "search_analyzer": "my_stop_analyzer", "search_quote_analyzer": "my_analyzer"},
                "source": {"type": "text", "index": "false"},
                "user_screen_name": {"type": "keyword", "similarity": "BM25", "normalizer": "my_normalizer"},
                "user_name": {"type": "wildcard"},
                "retweet_count": {"type": "integer", "index": "false", "ignore_malformed": "true"},
                "favorite_count": {"type": "integer", "index": "false", "ignore_malformed": "true"},
                "polarity": {"type": "keyword", "similarity": "BM25", "normalizer": "my_normalizer"},
                "text_vector": {"type": "dense_vector", "dims": 1024}
            }
		}
	}

    try:
        if es.indices.exists(index):
            es.indices.delete(index=index, ignore=[400, 404])
        
        es.indices.create(index=index, body=client_body, ignore=400)
    except Exception as e:
        print("\tError in index creation: ", e)

def create_user_profile_index():
    print("Create user profile index")

    '''
    client_body = {
        "settings": {
            "number_of_shards": 5,
            "number_of_replicas": 2
        },
        "mappings": {
            "properties": {
                "@joebiden": {"type": "dense_vector", "dims": 1024},
                "@barackobama": {"type": "dense_vector", "dims": 1024},
                "@kamalaharris": {"type": "dense_vector", "dims": 1024},
                "@justinbieber": {"type": "dense_vector", "dims": 1024},
                "@jbalvin": {"type": "dense_vector", "dims": 1024},
                "@diplo": {"type": "dense_vector", "dims": 1024}
            }
        }
    }
    '''
    client_body = {
        "settings": {
            "number_of_shards": 5,
            "number_of_replicas": 2
        },
        "mappings": {
            "properties": {
                "username": {"type": "keyword"},
                "user_vec": {"type": "dense_vector", "dims": 1024}
            }
        }
    }

    try:
        if es.indices.exists(userprofile_index):
            es.indices.delete(index=userprofile_index, ignore=[400, 404])

        es.indices.create(index=userprofile_index, body=client_body, ignore=400)

    except Exception as e:
        print("\tError in index creation: ", e)

def add_documents():
    def get_polarity(text):
        tweet = TextBlob(text)

        if(tweet.sentiment.polarity < 0):
            return 'negative'
        elif(tweet.sentiment.polarity == 0):
            return 'neutral'
        else:
            return 'positive'

    def get_tweet(tweet):
        doc = {
            "created_at": tweet[0],
            "id": tweet[1],
            "text": tweet[2],
            "hashtags": tweet[3],
            "mentions": tweet[4],
            "source": tweet[5],
            "user_screen_name": tweet[6],
            "user_name": tweet[7],
            "retweet_count": tweet[8],
            "favorite_count": tweet[9],
            "polarity": get_polarity(tweet[2]),
            "text_vector": tweet[10]
        }

        return doc

    def get_tweets(file):
        docs = 0
        allDocs = []

        with open(f'{file}', encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')

            for row in csv_reader:
                if docs != 0 and len(row) != 0:
                    doc = get_tweet(row)
                    if doc:
                        allDocs.append(doc)
                        docs += 1
                else:
                    docs += 1
            
        return allDocs

    print("Add documents")

    id = 0
    for user in users:
        print('\tIndexing ', user, ' tweets')
        allDocs = get_tweets(dir + user + '_tweets.csv')

        for i in range(0, len(allDocs)):
            allDocs[i]['text_vector'] = ast.literal_eval(allDocs[i]['text_vector'])

        for _, doc in enumerate(allDocs):
            es.index(index=index, id=id, body=doc)
            id = id + 1

def add_profile():
    print("Add users profile")

    id = 0
    for user in users:
        vec = sparse.load_npz("keywords_" + user + "_vec.npz")
        vec_list = vec[0].toarray().tolist()
        vec_list = vec_list[0]

        #doc = {user : vec_list}
        doc = {
            "username" : user, 
            "user_vec": vec_list
            }

        print('\tIndexing ', user, ' profile')

        es.index(index=userprofile_index, id=id, body=doc)
        id += 1

def search_exists(field, verbose=False):
    # returns documents that contain an indexed value for a field
    print("Search exists")

    res = es.search(body={'query': 
                                {'exists': 
                                    {"field": field}
                                }
                            })
    if verbose:
        print('\t', res)

    return res

def search_match(field, value, size=10, verbose=False):
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-query.html
    print("Search match")

    res = es.search(index=index, size=size, body={'query': 
                                    {'match': 
                                        {field: value}
                                    }
                                })
    if verbose:
        print('\t', res)

    return res

def search_prefix(field, value, size=10, verbose=False):
    print("Search prefix")

    res = es.search(index=index, size=size, body={'query': 
                                    {'prefix': 
                                        {field: value}
                                    }
                                })
    if verbose:
        print('\t', res)

    return res

def search_fuzzy(field, value, max_edit_distance='AUTO', verbose=False):
    print("Search fuzzy")

    res = es.search(index=index, body={'query': 
                                    {'fuzzy': 
                                        {field: 
                                            {
                                            'value': value,
                                            'fuzziness': max_edit_distance                                            }
                                        }
                                    }
                                })
    if verbose:
        print('\t', res)

    return res

def search_multi_fields(fields, value, size=10, type='best_fields', verbose=False):
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-multi-match-query.html
    # fields parameter must be a list
    # possible types = 'best_fields', 'most_fields', 'cross_fields', 'phrase', 'phrase_prefix', 'bool_prefix'
    print("Search multi-fields")

    res = es.search(index=index, size=size, body={'query':
                                    {'multi_match':
                                        {'query': value,
                                            'type': type,
                                            'fields': fields
                                        }
                                    }
                                })
    if verbose:
        print('\t', res)

    return res

def search_bool_multi_fields(fields, values, size=10, type="should", verbose=False):
    # fields and values parameters must be a list
    # possible types = 'must', 'should'
    print("Search bool multi-fields")

    query = []
    [query.append({'match': {'{}'.format(field): '{}'.format(value)}}) for field, value in zip(fields, values)]

    res = es.search(index=index, size=size, body={'query':
                                    {'bool':
                                        { type: query }
                                    }
                                })
    if verbose:
        print('\t', res) 

    return res

def search_regexp(field, value, case_insensitive=True, verbose=False):
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-regexp-query.html
    # https://en.wikipedia.org/wiki/Regular_expression
    print("Search regexp")

    res = es.search(index=index, body={'query': 
                                    {'regexp': 
                                        {field: 
                                            {
                                                'value': value,
                                                'case_insensitive': case_insensitive
                                            }
                                        }
                                    }
                                })
    if verbose:
        print('\t', res)

    return res

def search_wildcard(field, value, case_insensitive=True, verbose=False):
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-wildcard-query.html
    print("Search wildcard")

    res = es.search(index=index, body={'query': 
                                    {'wildcard': 
                                        {field: 
                                            {
                                                'value': value,
                                                'case_insensitive': case_insensitive
                                            }
                                        }
                                    }
                                })
    if verbose:
        print('\t', res)

    return res

def search_match_phrase(field, value, verbose=False):
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-query-phrase.html
    print("Search match phrase")

    res = es.search(index=index, body={'query': 
                                    {'match_phrase': 
                                        {field: value}
                                    }
                                })
    if verbose:
        print('\t', res)

    return res

def search_advanced_exists(field, verbose=False):
    print("Search exists personalized")

    results = []
    id = 0
    for user in users:
        res = es.get(index=userprofile_index, id=id)
        user_vec = res["_source"]["user_vec"]
        id += 1

        print("\tMatch for " + user + " profile")

        results.append(es.search(index=index, body={"query": {
                                                "script_score": {
                                                    "query": {
                                                        'exists': {"field": field}
                                                    },
                                                    "script": {
                                                        "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                                                        "params": {
                                                            "user_vector": user_vec
                                                        }
                                                    }
                                                }
                                            }}))

    if verbose:
        print('\t\t', results)
        
    return results

def search_advanced_match(field, value, size=10, verbose=False):
    print("Search match personalized")

    results = []
    id = 0
    for user in users:
        res = es.get(index=userprofile_index, id=id)
        user_vec = res["_source"]["user_vec"]
        id += 1

        print("\tMatch for " + user + " profile")

        results.append(es.search(index=index, size=size, body={"query": {
                                                "script_score": {
                                                    "query": {
                                                        'match': {field: value}
                                                    },
                                                    "script": {
                                                        "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                                                        "params": {
                                                            "user_vector": user_vec
                                                        }
                                                    }
                                                }
                                            }}))

    if verbose:
        print('\t\t', results)
        
    return results

def search_advanced_prefix(field, value, size=10, verbose=False):
    print("Search prefix personalized")

    results = []
    id = 0
    for user in users:
        res = es.get(index=userprofile_index, id=id)
        user_vec = res["_source"]["user_vec"]
        id += 1

        print("\tMatch for " + user + " profile")

        results.append(es.search(index=index, size=size, body={"query": {
                                                "script_score": {
                                                    "query": {
                                                        'prefix': {field: value}
                                                    },
                                                    "script": {
                                                        "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                                                        "params": {
                                                            "user_vector": user_vec
                                                        }
                                                    }
                                                }
                                            }}))

    if verbose:
        print('\t\t', results)
        
    return results

def search_advanced_fuzzy(field, value, max_edit_distance='AUTO', verbose=False):
    print("Search fuzzy personalized")

    results = []
    id = 0
    for user in users:
        res = es.get(index=userprofile_index, id=id)
        user_vec = res["_source"]["user_vec"]
        id += 1

        print("\tMatch for " + user + " profile")

        results.append(es.search(index=index, body={
            "query": {
                "script_score": {
                    'query': {
                        'fuzzy': {
                            field: {
                                'value': value,
                                'fuzziness': max_edit_distance
                            }
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                        "params": {
                            "user_vector": user_vec
                        }
                    }
                }
            }
        }))

    if verbose:
        print('\t\t', results)
        
    return results

def search_advanced_multi_fields(fields, value, size=10, type='best_fields', verbose=False):
    print("Search multi-fields personalized")

    results = []
    id = 0
    for user in users:
        res = es.get(index=userprofile_index, id=id)
        user_vec = res["_source"]["user_vec"]
        id += 1

        print("\tMatch for " + user + " profile")

        results.append(es.search(index=index, body={
            "query": {
                "script_score": {
                    'query': {
                        'multi_match': {
                            'query': value,
                            'type': type,
                            'fields': fields
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                        "params": {
                            "user_vector": user_vec
                        }
                    }
                }
            }
        }))

    if verbose:
        print('\t\t', results)
        
    return results

def search_advanced_bool_multi_fields(fields, values, size=10, type="should", verbose=False):
    print("Search bool multi-fields personalized")

    query = []
    [query.append({'match': {'{}'.format(field): '{}'.format(value)}}) for field, value in zip(fields, values)]

    results = []
    id = 0
    for user in users:
        res = es.get(index=userprofile_index, id=id)
        user_vec = res["_source"]["user_vec"]
        id += 1

        print("\tMatch for " + user + " profile")

        results.append(es.search(index=index, body={
            "query": {
                "script_score": {
                    'query': {
                        'bool': { 
                            type: query 
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                        "params": {
                            "user_vector": user_vec
                        }
                    }
                }
            }
        }))

    if verbose:
        print('\t\t', results)
        
    return results

def search_advanced_regexp(field, value, case_insensitive=True, verbose=False):
    print("Search regexp personalized")

    results = []
    id = 0
    for user in users:
        res = es.get(index=userprofile_index, id=id)
        user_vec = res["_source"]["user_vec"]
        id += 1

        print("\tMatch for " + user + " profile")

        results.append(es.search(index=index, body={
            "query": {
                "script_score": {
                    'query': {
                        'regexp': {
                            field: {
                                'value': value,
                                'case_insensitive': case_insensitive
                            }
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                        "params": {
                            "user_vector": user_vec
                        }
                    }
                }
            }
        }))

    if verbose:
        print('\t\t', results)
        
    return results

def search_advanced_wildcard(field, value, case_insensitive=True, verbose=False):
    print("Search wildcard personalized")

    results = []
    id = 0
    for user in users:
        res = es.get(index=userprofile_index, id=id)
        user_vec = res["_source"]["user_vec"]
        id += 1

        print("\tMatch for " + user + " profile")

        results.append(es.search(index=index, body={
            "query": {
                "script_score": {
                    'query': {
                        'wildcard': {
                            field: {
                                'value': value,
                                'case_insensitive': case_insensitive
                            }
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                        "params": {
                            "user_vector": user_vec
                        }
                    }
                }
            }
        }))

    if verbose:
        print('\t\t', results)
        
    return results

def search_advanced_match_phrase(field, value, verbose=False):
    print("Search match phrase personalized")

    results = []
    id = 0
    for user in users:
        res = es.get(index=userprofile_index, id=id)
        user_vec = res["_source"]["user_vec"]
        id += 1

        print("\tMatch for " + user + " profile")

        results.append(es.search(index=index, body={
            "query": {
                "script_score": {
                    'query': {
                        'match_phrase': {
                            field: value
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                        "params": {
                            "user_vector": user_vec
                        }
                    }
                }
            }
        }))

    if verbose:
        print('\t\t', results)
        
    return results

def test_search_exists():
    assert int(search_exists(field="text")['hits']['total']['value']) > 0
    assert int(search_exists(field="hashtags")['hits']['total']['value']) > 0
    assert int(search_exists(field="mentions")['hits']['total']['value']) > 0
    assert int(search_exists(field="user_screen_name")['hits']['total']['value']) > 0
    assert int(search_exists(field="user_name")['hits']['total']['value']) > 0
    assert int(search_exists(field="polarity")['hits']['total']['value']) > 0

def test_search_match():
    assert int(search_match(field="text", value="joe")['hits']['total']['value']) > 0
    assert int(search_match(field="hashtags", value="demconvention")['hits']['total']['value']) > 0
    assert int(search_match(field="mentions", value="kamalaharris")['hits']['total']['value']) > 0
    assert int(search_match(field="user_screen_name", value="joebiden")['hits']['total']['value']) > 0
    assert int(search_match(field="user_name", value="Joe Biden")['hits']['total']['value']) > 0
    assert int(search_match(field="polarity", value="PositivE")['hits']['total']['value']) > 0

def test_search_prefix():
    assert int(search_prefix(field="text", value="ame")['hits']['total']['value']) > 0
    assert int(search_prefix(field="hashtags", value="jo")['hits']['total']['value']) > 0
    assert int(search_prefix(field="mentions", value="kamala")['hits']['total']['value']) > 0
    assert int(search_prefix(field="user_screen_name", value="joebid")['hits']['total']['value']) > 0
    assert int(search_prefix(field="user_name", value="Joe B")['hits']['total']['value']) > 0
    assert int(search_prefix(field="polarity", value="pos")['hits']['total']['value']) > 0

def test_search_fuzzy():
    assert int(search_fuzzy(field="text", value="joi")['hits']['total']['value']) > 0
    assert int(search_fuzzy(field="hashtags", value="joi")['hits']['total']['value']) > 0
    assert int(search_fuzzy(field="mentions", value="joebidemm")['hits']['total']['value']) > 0
    assert int(search_fuzzy(field="user_screen_name", value="joebidemm")['hits']['total']['value']) > 0
    assert int(search_fuzzy(field="user_name", value="Joe Bidem")['hits']['total']['value']) > 0
    assert int(search_fuzzy(field="polarity", value="negati")['hits']['total']['value']) > 0

def test_search_multi_fields():
    assert int(search_multi_fields(fields=['text', 'user_screen_name'], value='joebiden', type='most_fields')['hits']['total']['value']) > 0
    assert int(search_multi_fields(fields=['mentions', 'user_screen_name'], value='joebiden', type='best_fields')['hits']['total']['value']) > 0
    assert int(search_multi_fields(fields=['text', 'mentions'], value='joebiden', type='cross_fields')['hits']['total']['value']) > 0
    assert int(search_multi_fields(fields=['text', 'hashtags'], value='joebiden', type='phrase')['hits']['total']['value']) > 0
    # multiplies the text field’s score by three but leaves the user_screen_name field’s score unchanged
    assert int(search_multi_fields(fields=['text^3', 'user_screen_name'], value='joebiden', type='most_fields')['hits']['total']['value']) > 0

def test_search_bool_multi_fields():
    assert int(search_bool_multi_fields(fields=['text', 'user_screen_name'], values=['stop', 'KamalaHarris'], type='must')['hits']['total']['value']) > 0
    assert int(search_bool_multi_fields(fields=['mentions', 'user_screen_name'], values=['stop', 'KamalaHarris'], type='should')['hits']['total']['value']) > 0
    assert int(search_bool_multi_fields(fields=['text', 'mentions'], values=['JoeBiden', 'KamalaHarris'], type='should')['hits']['total']['value']) > 0
    assert int(search_bool_multi_fields(fields=['user_screen_name', 'mentions'], values=['BarackObama', 'Ossoff'], type='must')['hits']['total']['value']) > 0
    # multiplies the text field’s score by three but leaves the user_screen_name field’s score unchanged
    assert int(search_bool_multi_fields(fields=['text^3', 'user_screen_name'], values=['JoeBiden', 'KamalaHarris'], type='should')['hits']['total']['value']) > 0

def test_search_regexp():
    assert int(search_regexp(field="text", value="j*e")['hits']['total']['value']) > 0
    assert int(search_regexp(field="hashtags", value="j.*")['hits']['total']['value']) > 0
    assert int(search_regexp(field="mentions", value="gre.*")['hits']['total']['value']) > 0
    assert int(search_regexp(field="user_screen_name", value="bar.*")['hits']['total']['value']) > 0
    assert int(search_regexp(field="user_name", value="ka.*")['hits']['total']['value']) > 0
    assert int(search_regexp(field="polarity", value="positive|negative")['hits']['total']['value']) > 0

def test_search_wildcard():
    assert int(search_wildcard(field="text", value="jo?")['hits']['total']['value']) > 0
    assert int(search_wildcard(field="hashtags", value="demconven*")['hits']['total']['value']) > 0
    assert int(search_wildcard(field="mentions", value="kamala*")['hits']['total']['value']) > 0
    assert int(search_wildcard(field="user_screen_name", value="joe?iden")['hits']['total']['value']) > 0
    assert int(search_wildcard(field="user_name", value="Joe*")['hits']['total']['value']) > 0
    assert int(search_wildcard(field="polarity", value="*ivE")['hits']['total']['value']) > 0

def test_search_match_phrase():
    assert int(search_match_phrase(field="text", value="joe biden")['hits']['total']['value']) > 0
    assert int(search_match_phrase(field="text", value="china")['hits']['total']['value']) > 0
    assert int(search_match_phrase(field="text", value="white house is")['hits']['total']['value']) == 0
    assert int(search_match_phrase(field="text", value="the balance of power")['hits']['total']['value']) == 0

def test_search_advanced_exists():
    results = search_advanced_exists(field="text")
    for r in results:
        assert int(r['hits']['total']['value']) > 0

def test_search_advanced_match():
    results = search_advanced_match(field="text", value="song")
    for r in results:
        assert int(r['hits']['total']['value']) > 0

def test_search_advanced_prefix():
    results = search_advanced_prefix(field="text", value="son")
    for r in results:
        assert int(r['hits']['total']['value']) > 0

def test_search_advanced_fuzzy():
    results = search_advanced_fuzzy(field="text", value="sonz")
    for r in results:
        assert int(r['hits']['total']['value']) > 0

def test_search_advanced_multi_fields():
    results = search_advanced_multi_fields(fields=['text'], value='song', type='most_fields')
    for r in results:
        assert int(r['hits']['total']['value']) > 0

def test_search_advanced_bool_multi_fields():
    results = search_advanced_bool_multi_fields(fields=['text'], values=['song', 'politic'], type='must')
    for r in results:
        assert int(r['hits']['total']['value']) > 0

def test_search_advanced_regexp():
    results = search_advanced_regexp(field="text", value="s*g")
    for r in results:
        assert int(r['hits']['total']['value']) > 0

def test_search_advanced_wildcard():
    results = search_advanced_wildcard(field="text", value="son?")
    for r in results:
        assert int(r['hits']['total']['value']) > 0

def test_search_advanced_match_phrase():
    results = search_advanced_match_phrase(field="text", value="joe biden")
    for r in results:
        assert int(r['hits']['total']['value']) > 0

if __name__ == "__main__":
    
    download_tweets()
    vectorize_texts()
    create_index()
    create_user_profile_index()
    add_documents()
    add_profile()

    # Simple query examples
    test_search_exists()
    test_search_match()
    test_search_prefix()
    test_search_fuzzy()
    test_search_multi_fields()
    test_search_bool_multi_fields()
    test_search_regexp()
    test_search_wildcard()
    test_search_match_phrase()
    
    # Advanced query examples
    test_search_advanced_exists()
    test_search_advanced_match()
    test_search_advanced_prefix()
    test_search_advanced_fuzzy()
    test_search_advanced_multi_fields()
    test_search_advanced_bool_multi_fields()
    test_search_advanced_regexp()
    test_search_advanced_wildcard()
    test_search_advanced_match_phrase()
    
