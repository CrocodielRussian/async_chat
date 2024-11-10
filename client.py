import tkinter as tk
import asyncio
from tkinter.scrolledtext import ScrolledText
from async_tkinter_loop import async_handler, async_mainloop


button_clicked = asyncio.Event()


@async_handler
async def async_function():
    button_clicked.set()

async def write_messages(writer, message_enter):
    while True:
        await button_clicked.wait()
        message = message_enter.get()
        message_enter.delete(0, tk.END)
        msg_bytes = message.encode()
        writer.write(msg_bytes)
        await writer.drain()
        button_clicked.clear()


async def receive_messages(reader, messages_widget):
    while True:
        data = await reader.read(100)
        message = data.decode()
        
        messages_widget.configure(state='normal')
        messages_widget.insert(tk.END, f"{message}\n")
        messages_widget.configure(state='disabled')
        messages_widget.see(tk.END)
   
async def main(messages, message_enter, login, room, chat):
    global loop, writer, reader

    if login == "":
        raise ValueError("Empty login")
    if room == "":
        raise ValueError("Empty room")
    raise_frame(chat)

    loop = asyncio.get_event_loop()
    print('Conecting to server...')
    reader, writer = await asyncio.open_connection(
        '127.0.0.2', 8888)
    
    print('Conected')

    receive_task = asyncio.create_task(receive_messages(reader, messages))

    await write_messages(writer, message_enter)

    receive_task.cancel()

    print('Disconnecting from server...')
    writer.close()
    await writer.wait_closed()
    print('Done.')
    
def raise_frame(frame):
    frame.tkraise()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Чат")
    root.geometry("500x500")
    root.resizable(0, 0)

    enter = tk.Frame(root)

    login_label = tk.Label(enter, text = "Логин")
    login_label.grid(row = 0, column=0, padx = 10, pady = 5, ipadx= 2, ipady= 2, sticky = "nse")
    login_entry = tk.Entry(enter)
    login_entry.grid(row = 0, column=1, padx = 10, pady = 5, ipadx= 2, ipady= 2, sticky = "news")


    room_label = tk.Label(enter, text = "Название комнаты")
    room_label.grid(row = 1, column=0, padx = 10, pady = 5, ipadx= 2, ipady= 2, sticky = "news")
    room_entry = tk.Entry(enter)
    room_entry.grid(row = 1, column=1, padx = 10, pady = 5, ipadx= 2, ipady= 2, sticky = "news")
    room_entry.insert(0, 'main')


    chat = tk.Frame(root)

    room = tk.Label(chat, text = "Комната " + room_entry.get())
    room.grid(row = 0, column = 0, padx = 10, pady = 5, ipadx= 10, ipady= 10, sticky = "news")

    exit = tk.Button(chat, text = "Выход", command = lambda: raise_frame(enter))
    exit.grid(row = 0, column=1, padx = 10, pady = 5, ipadx= 10, ipady= 10, sticky = "news")

    messages = ScrolledText(chat, width=50,  height=10, state='disabled')
    messages.grid(row = 1, column=0, columnspan=2, padx = 2, pady = 2, ipadx= 2, ipady= 2, sticky = "news")

    message_enter = tk.Entry(chat)
    message_enter.grid(row = 2, column=0, columnspan=2, padx = 10, pady = 5, ipadx= 2, ipady= 2, sticky = "news")

    send_message = tk.Button(chat, text="Отправить", command=async_function)
    send_message.grid(row=3, column=0, columnspan=2, padx=10, pady=5, ipadx=10, ipady=10, sticky="news")


    for frame in (enter, chat):
        frame.grid(row=0, column=0, sticky='nsew')

    submit = tk.Button(enter, text = "Войти", command = lambda: asyncio.create_task(main(messages, message_enter, login_entry.get(), room_entry.get(), chat)))
    submit.grid(row = 2, column=0, columnspan=2, padx = 10, pady = 5, ipadx= 10, ipady= 10, sticky = "news")


    raise_frame(enter)
    async_mainloop(root)

    