---
title: "Module 8: GraphQL and gRPC"
description: Compare query-shaped and service-shaped protocols.
---

REST is a useful public compatibility boundary, but it is not the only way to expose an API. GraphQL and gRPC solve different problems. Choose from the client interaction, ownership, performance, and operational constraints—not from novelty.

## Learning objectives

- explain how GraphQL’s schema and selection sets shape reads;
- explain protobuf contracts, generated clients, and gRPC status mapping;
- identify authorization, compatibility, and observability obligations in both;
- choose when REST remains the better boundary.

## GraphQL: client-shaped reads

GraphQL presents a typed schema and one endpoint. A client asks for exactly the fields it needs, such as `{ tasks { id title } }`, and the server returns a response shaped like that selection. This can prevent a collection of mobile-specific REST endpoints and reduce over-fetching. The example in `course/examples/graphql/server.py` is intentionally dependency-light: it accepts a POST body with a `query`, returns task data for a supported selection, and returns an error for an unsupported query.

That flexibility is also an attack surface. Limit query depth and field complexity, set a timeout, and reject introspection or expensive operations when the deployment requires it. Resolve authorization at the field or object boundary, not only at the endpoint. Prevent N+1 database calls with batching or a data-loader strategy. Give errors a stable shape while avoiding internal stack traces.

Run the example and client:

```bash
python course/examples/graphql/server.py
python course/examples/graphql/client.py
```

The server binds to `127.0.0.1:8010`; run the client from another terminal. Exercise: alter the query to request an unsupported field and observe the error contract. Then write a complexity rule that rejects a deeply nested query before any resolver runs.

## gRPC: service-shaped calls

gRPC is a strong fit for trusted service-to-service calls. Protobuf defines messages and methods, and generated clients make the contract explicit. Binary HTTP/2 transport supports streaming and efficient internal calls, while deadlines and metadata provide useful operational controls. The repository example is deliberately transport-neutral: `GetTaskRequest`, `Task`, and `TaskService.GetTask` show the shape without requiring a code-generation toolchain.

```bash
python course/examples/grpc/server.py
```

The example returns task 1 and raises a `NOT_FOUND`-shaped error for another ID. In a real server, map domain failures deliberately: `NOT_FOUND` for a missing task, `UNAUTHENTICATED` for absent or invalid identity, `PERMISSION_DENIED` for a valid caller without access, `INVALID_ARGUMENT` for malformed input, and `DEADLINE_EXCEEDED` when a deadline expires. Propagate a correlation ID in metadata and avoid logging credentials.

## Compatibility and selection

GraphQL schema evolution is usually additive: add fields, deprecate old ones, and preserve existing names and types. Protobuf evolution requires never reusing field numbers and treating removed fields as reserved. In either protocol, define timeouts, retry policy, pagination, and authorization as part of the contract. Retries need idempotency; a client retrying a mutation can otherwise duplicate work.

Keep REST when browser tooling, HTTP caching, simple curl access, public interoperability, or a stable resource URL matters. A platform may use all three: REST externally, GraphQL for a product UI gateway, and gRPC between internal services. Do not force clients through a protocol that obscures their deployment environment.

Think about ownership as well as transport. A GraphQL gateway often aggregates services and therefore needs per-field tracing, cache policy, and a clear rule for partial failures. A gRPC service should publish its protobuf and compatibility policy alongside generated code, with deadlines on every outbound call. In both cases, make cancellation reach the database or downstream service; otherwise a client timeout can leave expensive work running invisibly.

## Verification and next steps

Lab 08’s [README and examples](https://github.com/ialimustufa/API/tree/main/course/labs/08-graphql-grpc) are the source for the exercise. Verify that unsupported GraphQL queries fail predictably, authorization applies to returned objects, gRPC deadlines are honored, and domain errors map to the intended status. Record one case where REST is simpler and one where a typed internal method is worth gRPC’s tooling.

Next, use the interaction model to choose a streaming transport in [Module 9: Realtime delivery](../09-realtime/).
