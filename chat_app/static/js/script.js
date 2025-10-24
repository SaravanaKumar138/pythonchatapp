// Connect to server socket
const socket = io();

// join room right after connecting
socket.on("connect", () => {
  socket.emit("join", { username: USERNAME, room: ROOM });
});

// UI elements
const messagesDiv = document.getElementById("messages");
const usersList = document.getElementById("users");
const messageForm = document.getElementById("messageForm");
const msgInput = document.getElementById("msg");
const leaveBtn = document.getElementById("leaveBtn");
const typingDiv = document.getElementById("typing");

// helpers
function appendMessage(entry) {
  const el = document.createElement("div");
  el.classList.add("message");
  el.innerHTML = `<strong>${escapeHTML(entry.username)}</strong>: ${escapeHTML(
    entry.msg
  )}`;
  messagesDiv.appendChild(el);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function appendStatus(text) {
  const el = document.createElement("div");
  el.classList.add("status");
  el.textContent = text;
  messagesDiv.appendChild(el);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// basic client-side escape to avoid XSS from demo data
function escapeHTML(str) {
  if (!str) return "";
  return str.replace(
    /[&<>'"]/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "'": "&#39;",
        '"': "&quot;",
      }[c])
  );
}

// receive message
socket.on("message", (entry) => {
  appendMessage(entry);
});

// receive history (array of messages)
socket.on("history", (history) => {
  messagesDiv.innerHTML = "";
  history.forEach(appendMessage);
});

// status messages (join/leave)
socket.on("status", (data) => {
  if (data && data.msg) appendStatus(data.msg);
});

// user list update
socket.on("user_list", (users) => {
  usersList.innerHTML = "";
  users.forEach((u) => {
    const li = document.createElement("li");
    li.textContent = u;
    usersList.appendChild(li);
  });
});

// typing indicator
let typingTimeout = null;
socket.on("typing", (d) => {
  if (d.typing) {
    typingDiv.textContent = `${d.username} is typing...`;
  } else {
    typingDiv.textContent = "";
  }
});

// send message
messageForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = msgInput.value.trim();
  if (!text) return;
  socket.emit("message", { username: USERNAME, room: ROOM, msg: text });
  msgInput.value = "";
  socket.emit("typing", { username: USERNAME, room: ROOM, typing: false });
});

// typing events
msgInput.addEventListener("input", () => {
  socket.emit("typing", { username: USERNAME, room: ROOM, typing: true });
  if (typingTimeout) clearTimeout(typingTimeout);
  typingTimeout = setTimeout(() => {
    socket.emit("typing", { username: USERNAME, room: ROOM, typing: false });
  }, 1000);
});

// leave
leaveBtn.addEventListener("click", () => {
  socket.emit("leave", { username: USERNAME, room: ROOM });
  window.location.href = "/";
});
