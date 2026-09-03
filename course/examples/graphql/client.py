import json, urllib.request
request = urllib.request.Request("http://127.0.0.1:8010/graphql", json.dumps({"query": "{ tasks { id title } }"}).encode(), {"content-type": "application/json"})
print(urllib.request.urlopen(request).read().decode())
