# Lab 01: HTTP and API design

Learn to turn a small requirement into a predictable HTTP contract. This lab
uses no third-party packages: the contract is an OpenAPI document and the
solution includes a tiny standard-library server you can run and inspect.

## Run the solution

```bash
cd course/labs/01-http-api-design/solution
python server.py
```

In another terminal:

```bash
curl -i http://127.0.0.1:8001/api/v1/hello
curl -i -X POST http://127.0.0.1:8001/api/v1/echo \
  -H 'content-type: application/json' -d '{"message":"hello"}'
```

Read `openapi.yaml` first. The starter intentionally leaves the response
examples and error shape for you to complete. Compare it with the solution
after writing your own contract. Stop the server with Ctrl-C.

## Learning goals

- choose resource-oriented paths and HTTP methods;
- describe success and validation responses explicitly;
- return a stable JSON error shape (`type`, `title`, `status`, `detail`);
- keep a contract independent from an implementation.
