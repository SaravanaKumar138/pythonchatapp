from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import defaultdict, deque
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", secrets.token_hex(16))

# Use eventlet async mode
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory stores (replace with DB for production)
rooms_users = defaultdict(dict)  # rooms_users[room][sid] = username
rooms_history = defaultdict(lambda: deque(maxlen=200))  # last 200 messages per room

@app.route("/", methods=["GET"])
def index():
    # simple list of sample rooms
    rooms = ["General", "Developers", "Random"]
    return render_template("login.html", rooms=rooms)

@app.route("/chat", methods=["POST"])
def chat():
    username = request.form.get("username", "").strip()
    room = request.form.get("room", "").strip()
    if not username or not room:
        return redirect(url_for("index"))
    # store in session
    session["username"] = username
    session["room"] = room
    return render_template("chat.html", username=username, room=room)

# SocketIO events
@socketio.on("connect")
def handle_connect():
    # On connect we don't yet know the room until 'join' event is received.
    print("Client connected:", request.sid)

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    # remove user from any rooms they were in
    for room, users in list(rooms_users.items()):
        if sid in users:
            username = users.pop(sid, None)
            leave_room(room)
            # broadcast updated user list & leave message
            emit("user_list", list(users.values()), room=room)
            emit("status", {"msg": f"{username} left the room."}, room=room)
            print(f"{username} ({sid}) disconnected and removed from {room}")

@socketio.on("join")
def handle_join(data):
    # data: {"username": "...", "room": "..."}
    username = data.get("username")
    room = data.get("room")
    sid = request.sid
    if not username or not room:
        return
    join_room(room)
    rooms_users[room][sid] = username

    # send last messages to the new user only
    history = list(rooms_history[room])
    emit("history", history)

    # notify room
    emit("status", {"msg": f"{username} joined the room."}, room=room)
    # broadcast updated user list
    emit("user_list", list(rooms_users[room].values()), room=room)

@socketio.on("leave")
def handle_leave(data):
    username = data.get("username")
    room = data.get("room")
    sid = request.sid
    if room and sid in rooms_users[room]:
        rooms_users[room].pop(sid, None)
        leave_room(room)
        emit("status", {"msg": f"{username} left the room."}, room=room)
        emit("user_list", list(rooms_users[room].values()), room=room)

@socketio.on("message")
def handle_message(data):
    # data: {"username":"...","room":"...","msg":"..."}
    username = data.get("username")
    room = data.get("room")
    msg = data.get("msg", "").strip()
    if not room or not msg:
        return
    entry = {"username": username, "msg": msg}
    rooms_history[room].append(entry)
    emit("message", entry, room=room)

@socketio.on("typing")
def handle_typing(data):
    # data: {"username":"...", "room":"...", "typing": True/False}
    room = data.get("room")
    username = data.get("username")
    typing = data.get("typing", False)
    emit("typing", {"username": username, "typing": typing}, room=room, include_self=False)

if __name__ == "__main__":
    # Run with eventlet
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
