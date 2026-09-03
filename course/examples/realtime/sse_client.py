import httpx

with httpx.stream("GET", "http://127.0.0.1:8009/events") as response:
    for line in response.iter_lines():
        print(line)
