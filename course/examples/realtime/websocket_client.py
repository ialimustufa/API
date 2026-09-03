import asyncio, json
import websockets
async def main():
    async with websockets.connect("ws://127.0.0.1:8009/ws") as socket:
        await socket.send(json.dumps({"id": 1, "title": "updated"})); print(await socket.recv())
asyncio.run(main())
