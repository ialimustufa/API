# Lab 08: GraphQL and gRPC boundaries

Compare query-oriented GraphQL with contract-first gRPC. The examples are
deliberately dependency-light and show the boundary contracts, validation, and
error mapping. Run `python course/examples/graphql/server.py` and
`python course/examples/grpc/server.py`; use the included clients.

Discuss when each is appropriate: GraphQL is useful for client-shaped reads;
gRPC is efficient for trusted service-to-service calls. Keep REST as the
public compatibility boundary when browser and cache semantics matter.
