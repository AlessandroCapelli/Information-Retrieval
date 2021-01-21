# Information-Retrieval
## Alessandro Capelli

- Install Docker: https://docs.docker.com/engine/install/
- Make sure Docker Engine is allotted at least 4GiB of memory
- Run the docker-compose script to start ElasticSearch cluster, Kibana, SearchEngine and Web servers
- Web: http://localhost:5000/
- Kibana: http://localhost:5601/
- ElasticSearch: http://localhost:9200/
```
docker-compose build
docker-compose up
```

- Submit a _cat/nodes request to see that the nodes are up and running
```
curl -X GET "localhost:9200/_cat/nodes?v&pretty"
```

- Submit a tweets_index/_mapping request to see that the index is correct
```
curl -X GET "localhost:9200/tweets_index/_mapping?pretty"
```

- Try searching using the Web interface: http://localhost:5000/

- Stop the ElasticSearch, Kibana and Web servers and delete the data volumes
```
docker-compose down -v
```
