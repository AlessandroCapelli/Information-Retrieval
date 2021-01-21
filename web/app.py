from flask import Flask, render_template, request
from elasticsearch import Elasticsearch

app = Flask(__name__)
es = Elasticsearch("http://elasticsearch_1", port=9200)
index = "tweets_index"
users_index = "user_profile_index"

users_id = {}
users_id["JoeBiden"] = 0
users_id["BarackObama"] = 1
users_id["KamalaHarris"] = 2
users_id["JustinBieber"] = 3
users_id["JBalvin"] = 4
users_id["Diplo"] = 5

users_list = [
    "JoeBiden",
    "BarackObama",
    "KamalaHarris",
    "JustinBieber",
    "JBalvin",
    "Diplo"
]

@app.route("/")
def home():
    return render_template("search.html")


@app.route("/search/results", methods=["GET", "POST"])
def search_request():

    user = request.form.get("User")
    search_term = request.form["input"]
    query_type = request.form.get("queryType")
    field = request.form.get("fieldSearch")
    size = int(request.form.get("size"))
    
 
    if user in users_list:

        res = es.get(index=users_index, id=users_id[user])
        user_vec = res["_source"]["user_vec"]

        if field == "all":
            query_type = "multi-match"
            search_field = [
                "text",
                "hashtags",
                "mentions",
                "user_screen_name",
                "user_name",
                "polarity"
            ]
        elif field == "text":
            search_field = "text"
        elif field == "hashtags":
            search_field = "hashtags"
        elif field == "mentions":
            search_field = "mentions"
        elif field == "user_screen_name":
            search_field = "user_screen_name"
        elif field == "user_name":
            search_field = "user_name"
        else:
            search_field = "polarity"

        if query_type != "regexp" and len(search_field) == 1:
            res = es.search(
                index=index,
                size=size,
                body={
                    "query": {
                        "script_score": {
                            "query": {query_type: {search_field: search_term}},
                            "script": {
                                "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                                "params": {"user_vector": user_vec},
                            },
                        }
                    }
                },
            )

        elif query_type == "regexp":

            res = es.search(
                index=index,
                body={
                    "query": {
                        "script_score": {
                            "query": {
                                "regexp": {
                                    search_field: {
                                        "value": search_term,
                                        "case_insensitive": True,
                                    }
                                }
                            },
                            "script": {
                                "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                                "params": {"user_vector": user_vec},
                            },
                        }
                    }
                },
            )

        else:

            res = es.search(
                index=index,
                size=size,
                body={
                    "query": {
                        "script_score": {
                            "query": {
                                "multi_match": {
                                    "query": search_term,
                                    "type": "best_fields",
                                    "fields": search_field,
                                }
                            },
                            "script": {
                                "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                                "params": {"user_vector": user_vec},
                            },
                        }
                    }
                },
            )

        return render_template(
            "results.html",
            res=res,
            term=search_term,
            queryType=query_type,
            field=field,
            user_Name=user,
            single=True,
            pers = False
        )
    
    elif user == "All_users":
        
        if field == "all":
            query_type = "multi-match"
            search_field = [
                "text",
                "hashtags",
                "mentions",
                "user_screen_name",
                "user_name",
                "polarity"
            ]
        elif field == "text":
            search_field = "text"
        elif field == "hashtags":
            search_field = "hashtags"
        elif field == "mentions":
            search_field = "mentions"
        elif field == "user_screen_name":
            search_field = "user_screen_name"
        elif field == "user_name":
            search_field = "user_name"
        else:
            search_field = "polarity"
            
        if query_type != "regexp" and len(search_field) == 1:

            result = []
            for name in users_list:
                res = es.get(index=users_index, id=users_id[name])
                user_vec = res["_source"]["user_vec"]
                result.append(
                    es.search(
                        index=index,
                        size=size,
                        body={
                            "query": {
                                "script_score": {
                                    "query": {query_type: {search_field: search_term}},
                                    "script": {
                                        "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                                        "params": {"user_vector": user_vec},
                                    },
                                }
                            }
                        },
                    )
                )

        elif query_type == "regexp":

            result = []
            for name in users_list:
                res = es.get(index=users_index, id=users_id[name])
                user_vec = res["_source"]["user_vec"]
                result.append(
                    es.search(
                        index=index,
                        body={
                            "query": {
                                "script_score": {
                                    "query": {
                                        "regexp": {
                                            search_field: {
                                                "value": search_term,
                                                "case_insensitive": True,
                                            }
                                        }
                                    },
                                    "script": {
                                        "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                                        "params": {"user_vector": user_vec},
                                    },
                                }
                            }
                        },
                    )
                )

        else:

            result = []
            for name in users_list:
                res = es.get(index=users_index, id=users_id[name])
                user_vec = res["_source"]["user_vec"]
                result.append(
                    es.search(
                        index=index,
                        size=size,
                        body={
                            "query": {
                                "script_score": {
                                    "query": {
                                        "multi_match": {
                                            "query": search_term,
                                            "type": "best_fields",
                                            "fields": search_field,
                                        }
                                    },
                                    "script": {
                                        "source": "cosineSimilarity(params.user_vector, 'text_vector') + 1.0",
                                        "params": {"user_vector": user_vec},
                                    },
                                }
                            }
                        },
                    )
                )

        return render_template(
            "results.html",
            res=result,
            term=search_term,
            queryType=query_type,
            field=field,
            user_Name="all",
            single=False,
            pers=False,
            users_list=users_list
        )
   
    elif user == "None":

        if field == "all":
            query_type = "multi-match"
            search_field = [
                "text",
                "hashtags",
                "mentions",
                "user_screen_name",
                "user_name",
                "polarity"
            ]
        elif field == "text":
            search_field = "text"
        elif field == "hashtags":
            search_field = "hashtags"
        elif field == "mentions":
            search_field = "mentions"
        elif field == "user_screen_name":
            search_field = "user_screen_name"
        elif field == "user_name":
            search_field = "user_name"
        else:
            search_field = "polarity"

        if query_type != "regexp" and len(search_field) == 1:
            res = es.search(
                index=index,
                size=size,
                body={"query": {query_type: {search_field: search_term}}},
            )
        elif query_type == "regexp":
            res = es.search(
                index=index,
                body={"query": {"regexp": {search_field: {"value": search_term}}}},
            )
        else:
            res = es.search(
                index=index,
                size=size,
                body={
                    "query": {
                        "multi_match": {"query": search_term, "fields": search_field}
                    }
                },
            )

        return render_template(
            "results.html",
            res=res,
            term=search_term,
            queryType=query_type,
            field=field,
            user_Name="none",
            single=True,
            pers=True
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
