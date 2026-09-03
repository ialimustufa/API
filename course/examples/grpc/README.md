# Protocol examples

The GraphQL example accepts a JSON POST with a query and returns the standard
`data`/`errors` envelope. The gRPC example models a protobuf request/response
and maps a missing resource to `NOT_FOUND`; in a full service, generate the
wire server from a `.proto` file and never hand-edit generated code.
