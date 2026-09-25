import asyncio
import json
import os
import websockets

rooms = {}


async def send_room_list(websocket):
    await websocket.send(json.dumps({
        "type": "room_list",
        "rooms": list(rooms.keys())
    }))


async def broadcast_room_list():
    clients = set()

    for room_clients in rooms.values():
        clients.update(room_clients)

    message = json.dumps({
        "type": "room_list",
        "rooms": list(rooms.keys())
    })

    for client in clients.copy():
        try:
            await client.send(message)
        except:
            pass


async def chat(websocket):
    current_room = None

    try:
        await send_room_list(websocket)

        async for message in websocket:
            try:
                data = json.loads(message)
            except:
                continue

            msg_type = data.get("type")

            # 방 만들기
            if msg_type == "create":
                room = data.get("room", "").strip()

                if not room:
                    continue

                if room in rooms:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "이미 존재하는 방입니다."
                    }))
                    continue

                rooms[room] = set()
                rooms[room].add(websocket)
                current_room = room

                await websocket.send(json.dumps({
                    "type": "joined",
                    "room": room
                }))

                await broadcast_room_list()

            # 방 입장
            elif msg_type == "join":
                room = data.get("room", "").strip()

                if room not in rooms:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "없는 방입니다."
                    }))
                    continue

                if current_room and current_room in rooms:
                    rooms[current_room].discard(websocket)

                    if not rooms[current_room]:
                        del rooms[current_room]

                rooms[room].add(websocket)
                current_room = room

                await websocket.send(json.dumps({
                    "type": "joined",
                    "room": room
                }))

                await broadcast_room_list()

            # 메시지 보내기
            elif msg_type == "message":
                text = data.get("text", "").strip()

                if not current_room or current_room not in rooms:
                    continue

                if not text:
                    continue

                message_data = json.dumps({
                    "type": "message",
                    "text": text
                })

                for client in rooms[current_room].copy():
                    try:
                        await client.send(message_data)
                    except:
                        rooms[current_room].discard(client)

    except websockets.exceptions.ConnectionClosed:
        pass

    finally:
        if current_room and current_room in rooms:
            rooms[current_room].discard(websocket)

            if not rooms[current_room]:
                del rooms[current_room]

        await broadcast_room_list()


async def main():
    port = int(os.environ.get("PORT", 8080))

    async with websockets.serve(
        chat,
        "0.0.0.0",
        port
    ):
        print(f"엔톡 서버 실행 중! 포트: {port}")
        await asyncio.Future()


asyncio.run(main())
