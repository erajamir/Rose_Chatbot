import openai
import tkinter as tk
from tkinter import scrolledtext
import speech_recognition as sr
import pyttsx3
import threading

import os
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

BOT_NAME = "Rose"
chat_sessions = []

def create_new_chat():
    chat_sessions.append({
        "title": f"Chat {len(chat_sessions)+1}",
        "memory": [{"role": "system", "content": f"You are {BOT_NAME}, a helpful assistant."}],
        "named": False
    })

def get_current_chat():
    return chat_sessions[current_chat_index]

def chat_with_gpt(prompt, memory=[]):
    if BOT_NAME.lower() in prompt.lower():
        prompt = f"You are called {BOT_NAME}. Respond accordingly.\nUser said: {prompt}"

    memory.append({"role": "user", "content": prompt})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=memory
    )
    reply = response['choices'][0]['message']['content']
    memory.append({"role": "assistant", "content": reply})
    return reply, memory

def get_chat_title(first_message):
    prompt = f"Give me a very short (2-4 words) descriptive title for a chat where the user said: \"{first_message}\". Only return the title."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that gives short chat titles."},
            {"role": "user", "content": prompt}
        ]
    )
    title = response['choices'][0]['message']['content'].strip().strip('"').strip("'")
    return title if title else "Chat"

engine = pyttsx3.init()
voices = engine.getProperty('voices')
female_voice = None
for voice in voices:
    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
        female_voice = voice.id
        break
engine.setProperty('voice', female_voice if female_voice else voices[0].id)

def speak(text):
    engine.say(text)
    engine.runAndWait()

def speak_async(text):
    threading.Thread(target=speak, args=(text,), daemon=True).start()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            audio = r.listen(source, timeout=5)
            query = r.recognize_google(audio)
            entry.delete(0, tk.END)
            entry.insert(0, query)
            send_message()
        except Exception:
            pass

def send_message(event=None):
    user_msg = entry.get()
    if user_msg and user_msg != placeholder_text:
        chat = get_current_chat()
        if not chat["named"]:
            chat["title"] = get_chat_title(user_msg)
            chat["named"] = True
            refresh_chat_list()

        chat_window.insert(tk.END, "You: " + user_msg + "\n")
        chat_window.see(tk.END)
        entry.delete(0, tk.END)
        add_placeholder()

        bot_reply, updated_memory = chat_with_gpt(user_msg, chat["memory"])
        chat["memory"] = updated_memory

        chat_window.insert(tk.END, f"{BOT_NAME}: " + bot_reply + "\n\n")
        chat_window.see(tk.END)
        speak_async(bot_reply)

def load_chat(index):
    global current_chat_index
    current_chat_index = index
    chat_window.config(state=tk.NORMAL)
    chat_window.delete('1.0', tk.END)
    chat = chat_sessions[index]
    for msg in chat["memory"]:
        if msg["role"] == "user":
            chat_window.insert(tk.END, "You: " + msg["content"] + "\n")
        elif msg["role"] == "assistant":
            chat_window.insert(tk.END, f"{BOT_NAME}: " + msg["content"] + "\n\n")
    chat_window.see(tk.END)

def refresh_chat_list():
    chat_listbox.delete(0, tk.END)
    for i, chat in enumerate(chat_sessions):
        title = chat["title"]
        if i == current_chat_index:
            title = "> " + title
        chat_listbox.insert(tk.END, title)

def new_chat_clicked():
    create_new_chat()
    global current_chat_index
    current_chat_index = len(chat_sessions) - 1
    refresh_chat_list()
    load_chat(current_chat_index)
    add_placeholder()

def add_placeholder(event=None):
    if entry.get() == '':
        entry.insert(0, placeholder_text)
        entry.config(fg='gray')

def remove_placeholder(event=None):
    if entry.get() == placeholder_text:
        entry.delete(0, tk.END)
        entry.config(fg='white')

# --- Init ---
create_new_chat()
current_chat_index = 0

root = tk.Tk()
root.title("Chat with Rose")
root.geometry("800x600")
root.config(bg="#2e2e2e")

left_frame = tk.Frame(root, width=200, bg="#1e1e1e")
left_frame.pack(side=tk.LEFT, fill=tk.Y)

# Beautiful New Chat Button
new_chat_btn = tk.Button(
    left_frame, text="+ New Chat", command=new_chat_clicked,
    bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
    relief=tk.FLAT, activebackground="#45a049", activeforeground="white",
    cursor="hand2", bd=0
)
new_chat_btn.pack(fill=tk.X, padx=5, pady=5)

chat_listbox = tk.Listbox(
    left_frame, bg="#2e2e2e", fg="white", font=("Arial", 12),
    selectbackground="#4CAF50", activestyle="none",
    highlightthickness=0, bd=0
)
chat_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
chat_listbox.bind("<<ListboxSelect>>", lambda evt: load_chat(chat_listbox.curselection()[0]) if chat_listbox.curselection() else None)

right_frame = tk.Frame(root, bg="#2e2e2e")
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

heading = tk.Label(right_frame, text="How can I help you today?", font=("Helvetica", 18, "bold"), fg="white", bg="#2e2e2e")
heading.pack(pady=10)

chat_window = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=("Arial", 12), bg="#1e1e1e", fg="white", state=tk.NORMAL)
chat_window.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

input_frame = tk.Frame(right_frame, bg="#2e2e2e")
input_frame.pack(padx=10, pady=10, fill=tk.X)

placeholder_text = 'Write Something....'
entry = tk.Entry(input_frame, font=("Arial", 14), bg="#3e3e3e", fg="gray", insertbackground="white")
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
entry.insert(0, placeholder_text)
entry.bind("<FocusIn>", remove_placeholder)
entry.bind("<FocusOut>", add_placeholder)
entry.bind("<Return>", send_message)

# Beautiful Send Button
send_button = tk.Button(
    right_frame, text="➤ Send", command=send_message,
    bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
    relief=tk.FLAT, activebackground="#45a049", activeforeground="white",
    cursor="hand2", bd=0, padx=20, pady=6
)
send_button.pack(pady=5)

mic_button = tk.Button(input_frame, text="🎤", command=listen, bg="#555555", fg="white", font=("Arial", 14), relief=tk.FLAT, padx=10)
mic_button.pack(side=tk.LEFT, padx=(5,0))

refresh_chat_list()
load_chat(current_chat_index)

root.mainloop()
