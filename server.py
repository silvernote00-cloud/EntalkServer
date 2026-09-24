import asyncio
import websockets
import json

clients = set()
rooms = {}


async def send_room_list():
    data = json.dumps({
        "type": "rooms",
        "rooms": list(rooms.keys())
    })

    for client in clients.copy():
        try:
            await client.send(data)
        except:
            pass


async def chat(websocket):

    clients.add(websocket)

    current_room = None

    try:

        async for message in websocket:

            data = json.loads(message)

            # =========================
            # 방 만들기
            # =========================

            if data["type"] == "create":

                room = data["room"].strip()

                if room == "":
                    continue

                if room not in rooms:
                    rooms[room] = set()

                # 기존 방에서 나가기
                if current_room is not None:
                    rooms[current_room].discard(websocket)

                    if len(rooms[current_room]) == 0:
                        del rooms[current_room]

                current_room = room
                rooms[room].add(websocket)

                await websocket.send(json.dumps({
                    "type": "joined",
                    "room": room
                }))

                await send_room_list()


            # =========================
            # 방 입장
            # =========================

            elif data["type"] == "join":

                room = data["room"]

                if room not in rooms:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "text": "존재하지 않는 방이야!"
                    }))
                    continue

                # 기존 방에서 나가기
                if current_room is not None:
                    rooms[current_room].discard(websocket)

                    if len(rooms[current_room]) == 0:
                        del rooms[current_room]

                current_room = room
                rooms[room].add(websocket)

                await websocket.send(json.dumps({
                    "type": "joined",
                    "room": room
                }))


            # =========================
            # 메시지 보내기
            # =========================

            elif data["type"] == "message":

                room = data["room"]
                text = data["text"]

                if room not in rooms:
                    continue

                for client in rooms[room].copy():

                    try:
                        await client.send(json.dumps({
                            "type": "message",
                            "text": text
                        }))
                    except:
                        pass


            # =========================
            # 방 나가기
            # =========================

            elif data["type"] == "leave":

                if current_room is not None:

                    rooms[current_room].discard(websocket)

                    if len(rooms[current_room]) == 0:
                        del rooms[current_room]

                    current_room = None

                    await websocket.send(json.dumps({
                        "type": "left"
                    }))

                    await send_room_list()


    finally:

        clients.discard(websocket)

        if current_room is not None:

            rooms[current_room].discard(websocket)

            if len(rooms[current_room]) == 0:
                del rooms[current_room]

            await send_room_list()


async def main():

    async with websockets.serve(
        chat,
        "0.0.0.0",
        8080
    ):

        print("엔톡 서버 실행 중!")
        print("포트: 8080")

        await asyncio.Future()


asyncio.run(main())