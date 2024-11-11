import asyncio
import re

async def write_message(writer, data):
    writer.write(data)
    await writer.drain()

async def connect_user(reader, writer):
    global ALL_USERS

    name_bytes = await reader.read(100)
    data = name_bytes.decode().strip().split()
    name = data[0]
    group = data[1]

    ALL_USERS[name] = (reader, writer, group)

    print(ALL_USERS[name])

    await broadcast_message(f'{name} has connected', group)

    welcome = f'Welcome {name}.'
    writer.write(welcome.encode())
    await writer.drain()


    return name, group

async def handle_chat_client(reader, writer):
    name, group = await connect_user(reader, writer)
    try:
        while True:
            data = await reader.read(100)
            message = data.decode()

            if message == "QUIT":
                # print("try disconnect")
                break

            addr = writer.get_extra_info('peername')
            print(f"Received {message!r} from {addr!r}")

            message = f"[{name}] {message}"

            await broadcast_message(message, group)
    finally:
        await disconnect_user(name, group, writer)

async def broadcaster():
    global queue, ALL_USERS

    while True:
        packet = await queue.get()
        message = packet[0]

        private_users = re.findall(r'\[(.*?)\]', message)
        author = packet[1]
        print(f'Broadcast: {message.strip()}')
        msg_bytes = message.encode()

        tasks = []
        if(len(private_users) > 1):
            print(private_users)
            tasks = [asyncio.create_task(write_message(w, msg_bytes)) if(room == author and user == private_user) else asyncio.create_task(asyncio.sleep(0)) for user,(_,w, room) in ALL_USERS.items() for private_user in private_users]
        else:
            print("open")
            tasks = [asyncio.create_task(write_message(w, msg_bytes)) if(room == author) else asyncio.create_task(asyncio.sleep(0)) for _,(_,w, room) in ALL_USERS.items()]

        _ = await asyncio.wait(tasks)

async def broadcast_message(message, author):
    global queue
    await queue.put((message, author))

async def disconnect_user(name, group, writer):
    global ALL_USERS

    writer.close()
    await writer.wait_closed()

    del ALL_USERS[name]
    
    await broadcast_message(f'{name} has disconnected', group)

async def main():
    broadcaster_task = asyncio.create_task(broadcaster())

    server = await asyncio.start_server(
        handle_chat_client, '127.0.0.2', 8888)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

ALL_USERS = {}

queue = asyncio.Queue()

asyncio.run(main())