"""A transport-neutral gRPC-shaped service contract for the lesson."""

from dataclasses import dataclass


@dataclass
class GetTaskRequest:
    id: int


@dataclass
class Task:
    id: int
    title: str


class TaskService:
    def GetTask(self, request: GetTaskRequest) -> Task:
        if request.id != 1:
            raise KeyError("NOT_FOUND")
        return Task(1, "Learn gRPC")


if __name__ == "__main__":
    print(TaskService().GetTask(GetTaskRequest(1)))
