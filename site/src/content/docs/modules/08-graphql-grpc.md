---
title: "Module 8: GraphQL and gRPC"
description: Compare query-shaped and service-shaped protocols.
---

GraphQL exposes a typed schema and lets clients select fields, making it useful for client-shaped reads; enforce depth, complexity, authorization, and query timeouts. gRPC uses protobuf contracts and generated clients, making it a strong fit for internal calls; map status codes deliberately (`NOT_FOUND`, `UNAUTHENTICATED`, `PERMISSION_DENIED`). Version schemas compatibly and keep REST where browser, caching, or public interoperability is the priority.

Run the examples in `course/examples/graphql` and `course/examples/grpc`.
