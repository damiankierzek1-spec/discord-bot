import discord
from discord.ext import commands
from discord import Intents, utils, Embed, File
from discord.ui import Button, View, Modal, TextInput
import os
from flask import Flask, render_template_string, request, redirect, session, jsonify, Response
from threading import Thread
import asyncio
import io
from datetime import datetime
from typing import List
import json

# ===============================
# 🚨 KONFIGURACJA GLOBALNA I ZMIENNE ŚRODOWISKOWE 🚨
# ===============================

ADMIN_IDS: List[int] = [652507356105539585, 550959315700154368, 590215623259193371]
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PWD", "Kuba123!")
ARCHIVE_FILE = "ticket_archive.json"

app = Flask('')
app.secret_key = os.environ.get("FLASK_SECRET", "super-tajny-klucz-kubusiowo")

bot_instance = None
ticket_data_cache = {}
web_listeners = []

# Ładowanie archiwum z pliku JSON przy starcie
def load_archive():
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return []
    return []

def save_to_archive(data):
    archive = load_archive()
    archive.append(data)
    with open(ARCHIVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(archive, f, ensure_ascii=False, indent=4)

# ===============================
# 🎨 STYLE CSS DLA STRONY WWW
# ===============================

SHARED_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    body { font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #0a0813 0%, #110d22 50%, #050307 100%); color: #e2e8f0; min-height: 100vh; margin: 0; }
    .dashboard-container { display: flex; min-height: 100vh; }
    .sidebar { width: 260px; background: rgba(15, 12, 30, 0.6); border-right: 1px solid rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); padding: 2rem 1.5rem; display: flex; flex-direction: column; justify-content: space-between; }
    .main-content { flex: 1; padding: 2.5rem; overflow-y: auto; }
    .menu-list a { color: #a0aec0; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 10px; transition: all 0.3s ease; font-weight: 500; }
    .menu-list a:hover, .menu-list a.is-active { background: rgba(88, 101, 242, 0.15); color: #fff; text-shadow: 0 0 10px rgba(88, 101, 242, 0.5); border-left: 4px solid #5865f2; padding-left: 12px; }
    .glass-box { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 16px; backdrop-filter: blur(12px); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); }
    .glow-text { color: #fff; text-shadow: 0 0 12px rgba(88, 101, 242, 0.6); }
    .btn-glow { background: linear-gradient(45deg, #7289da, #5865f2); color: white; border: none; font-weight: 600; border-radius: 8px; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(88, 101, 242, 0.3); }
    .btn-glow:hover { background: linear-gradient(45deg, #5865f2, #4752c4); transform: scale(1.02); box-shadow: 0 6px 20px rgba(88, 101, 242, 0.5); color: white; }
    .btn-danger-glow { background: linear-gradient(45deg, #ff4757, #ee5253); color: white; border: none; font-weight: 600; border-radius: 8px; transition: all 0.3s ease; }
    .btn-danger-glow:hover { transform: scale(1.02); box-shadow: 0 6px 20px rgba(238, 82, 83, 0.4); }
    .custom-input { background: rgba(0, 0, 0, 0.3) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; color: #fff !important; border-radius: 8px !important; }
    .custom-select select { background: rgba(0, 0, 0, 0.3) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; color: #fff !important; border-radius: 8px !important; }
    .tab-content { display: none; animation: fadeIn 0.4s ease forwards; }
    .tab-content.is-active { display: block; }
    .notification { background: rgba(46, 213, 115, 0.12) !important; border: 1px solid rgba(46, 213, 115, 0.4) !important; color: #2ed573 !important; border-radius: 8px; }
    .ticket-badge { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); padding: 12px 20px; border-radius: 10px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

    /* Style czatu */
    .chat-container { display: flex; height: 600px; gap: 20px; }
    .chat-channels-list { width: 250px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
    .chat-channel-item { padding: 12px; border-radius: 8px; cursor: pointer; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); }
    .chat-channel-item:hover, .chat-channel-item.active { background: rgba(88, 101, 242, 0.15); border-color: #5865f2; color: #fff; }
    .chat-window { flex: 1; display: flex; flex-direction: column; height: 100%; position: relative; }
    .chat-messages { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); }
    .chat-msg-row { display: flex; flex-direction: column; max-width: 75%; padding: 8px 12px; border-radius: 8px; word-break: break-word; }
    .chat-msg-row.bot { background: rgba(88, 101, 242, 0.2); border: 1px solid rgba(88, 101, 242, 0.4); align-self: flex-end; }
    .chat-msg-row.user { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); align-self: flex-start; }
    .chat-msg-author { font-size: 0.75rem; font-weight: bold; color: #a0aec0; margin-bottom: 2px; }
    .chat-msg-time { font-size: 0.65rem; color: #718096; align-self: flex-end; margin-top: 4px; }
    .chat-input-area { display: flex; gap: 10px; margin-top: 15px; }

    /* Style bazy użytkowników i archiwum */
    .user-split { display: flex; gap: 20px; height: 650px; }
    .user-list-side { width: 300px; overflow-y: auto; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); }
    .user-list-item { display: flex; align-items: center; gap: 10px; padding: 8px; border-radius: 6px; cursor: pointer; margin-bottom: 5px; background: rgba(255,255,255,0.01); transition: all 0.2s; }
    .user-list-item:hover, .user-list-item.active { background: rgba(88, 101, 242, 0.15); color: #fff; }
    .user-list-item img { width: 32px; height: 32px; border-radius: 50%; }
    .user-profile-side { flex: 1; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 25px; border-radius: 12px; overflow-y: auto; }
    .role-tag { display: inline-block; background: rgba(88,101,242,0.2); border: 1px solid #5865f2; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; margin: 3px; }
    .archive-item { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
</style>
"""

# ===============================
# 📄 SZABLONY HTML WWW
# ===============================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubusiowo - Panel</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    {{ SHARED_STYLE | safe }}
</head>
<body>
    <div class="dashboard-container">
        <aside class="sidebar">
            <div>
                <div class="has-text-centered mb-6">
                    <h1 class="title is-4 glow-text mb-1">🎮 KUBUSIOWO</h1>
                    <p class="is-size-7 has-text-grey">v8.0 Master System</p>
                </div>
                <ul class="menu-list">
                    <li><a href="#" class="is-active" onclick="switchTab(event, 'status-tab')">⚙️ Status bota</a></li>
                    <li><a href="#" onclick="switchTab(event, 'management-tab')">🛠️ Stwórz Kanał</a></li>
                    <li><a href="#" onclick="switchTab(event, 'users-tab')">👥 Baza Użytkowników</a></li>
                    <li><a href="#" onclick="switchTab(event, 'tickets-tab')">🎫 Aktywne Tickety</a></li>
                    <li><a href="#" onclick="switchTab(event, 'chat-tab')">💬 Czat Ticketów</a></li>
                    <li><a href="#" onclick="switchTab(event, 'archive-tab')">📜 Archiwum Ticketów</a></li>
                </ul>
            </div>
            <div><a href="/logout" class="button btn-danger-glow is-fullwidth">Wyloguj się</a></div>
        </aside>

        <main class="main-content">
            <div id="status-tab" class="tab-content is-active">
                <div class="box glass-box p-6 mb-5">
                    <h2 class="title is-3 has-text-white mb-2">Ustawienia Aktywności</h2>
                    <form method="POST" action="/update-status">
                        <div class="field mb-4">
                            <input class="input custom-input" type="text" name="status_text" value="{{ current_status }}">
                        </div>
                        <button type="submit" class="button btn-glow px-5">Zaktualizuj status</button>
                    </form>
                </div>
            </div>

            <div id="management-tab" class="tab-content">
                <div class="box glass-box p-5" style="max-width: 500px;">
                    <h3 class="title is-4 has-text-white mb-3">📁 Stwórz Nowy Kanał na Serwerze</h3>
                    <form method="POST" action="/create-channel">
                        <div class="field mb-3"><input class="input custom-input" type="text" name="channel_name" required placeholder="nazwa kanału"></div>
                        <div class="field mb-4"><div class="select is-fullwidth custom-select"><select name="channel_type"><option value="text">Tekstowy</option><option value="voice">Głosowy</option></select></div></div>
                        <button type="submit" class="button btn-glow is-fullwidth">Stwórz</button>
                    </form>
                </div>
            </div>

            <div id="users-tab" class="tab-content">
                <div class="box glass-box p-5">
                    <h2 class="title is-4 has-text-white mb-4">👥 Menedżer Użytkowników Discorda</h2>
                    <div class="user-split">
                        <div id="user-list" class="user-list-side"><p class="has-text-grey">Ładowanie użytkowników...</p></div>
                        <div id="user-profile" class="user-profile-side">
                            <p class="has-text-grey has-text-centered" style="margin-top: 150px;">Wybierz osobę z listy po lewej, aby zarządzać profilem.</p>
                        </div>
                    </div>
                </div>
            </div>

            <div id="tickets-tab" class="tab-content">
                <div class="box glass-box p-6">
                    <h2 class="title is-3 has-text-white mb-2">🎫 Monitor Otwartych Zgłoszeń</h2>
                    <div id="tickets-list"><p class="has-text-grey">Ładowanie...</p></div>
                </div>
            </div>

            <div id="chat-tab" class="tab-content">
                <div class="box glass-box p-5">
                    <h2 class="title is-4 has-text-white mb-4">💬 Live Chat - Pisz jako BOT</h2>
                    <div class="chat-container">
                        <div id="chat-channels" class="chat-channels-list"><p class="has-text-grey is-size-7">Ładowanie...</p></div>
                        <div class="chat-window">
                            <div id="chat-messages" class="chat-messages">
                                <p class="has-text-grey" style="margin:auto;">Wybierz ticket z listy po lewej stronie.</p>
                            </div>
                            <div class="chat-input-area">
                                <input type="text" id="chat-input-msg" class="input custom-input" placeholder="Wpisz wiadomość jako Bot..." disabled onkeydown="if(event.key==='Enter') sendWebMessage()">
                                <button id="chat-send-btn" class="button btn-glow" disabled onclick="sendWebMessage()">Wyślij</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div id="archive-tab" class="tab-content">
                <div class="box glass-box p-5">
                    <h2 class="title is-4 has-text-white mb-4">📜 Lokalne Archiwum Transkrypcji WWW</h2>
                    <div id="archive-list"><p class="has-text-grey">Ładowanie archiwum...</p></div>
                </div>
            </div>
        </main>
    </div>

    <script>
        let currentActiveChannelId = null;
        let selectedUserId = null;

        function switchTab(evt, tabId) {
            document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("is-active"));
            document.querySelectorAll(".menu-list a").forEach(el => el.classList.remove("is-active"));
            document.getElementById(tabId).classList.add("is-active");
            evt.currentTarget.classList.add("is-active");
            if (tabId === 'tickets-tab') fetchTickets();
            if (tabId === 'chat-tab') fetchChatChannels();
            if (tabId === 'users-tab') fetchUsers();
            if (tabId === 'archive-tab') fetchArchive();
        }

        function fetchTickets() {
            const listDiv = document.getElementById('tickets-list');
            fetch('/api/tickets').then(res => res.json()).then(data => {
                listDiv.innerHTML = '';
                if (data.length === 0) { listDiv.innerHTML = '<p class="has-text-grey-light">Brak ticketów.</p>'; return; }
                data.forEach(t => {
                    const div = document.createElement('div');
                    div.className = 'ticket-badge';
                    div.innerHTML = `<div><strong style="color:#fff;">#${t.name}</strong></div>
                    <form method="POST" action="/close-ticket-dash" style="margin:0;"><input type="hidden" name="channel_id" value="${t.id}"><button type="submit" class="button is-small btn-danger-glow px-4">Zamknij i Zarchiwizuj</button></form>`;
                    listDiv.appendChild(div);
                });
            });
        }

        function fetchChatChannels() {
            const channelsDiv = document.getElementById('chat-channels');
            fetch('/api/tickets').then(res => res.json()).then(data => {
                channelsDiv.innerHTML = '';
                if(data.length === 0){ channelsDiv.innerHTML = '<p class="has-text-grey is-size-7">Brak otwartych ticketów.</p>'; return; }
                data.forEach(t => {
                    const div = document.createElement('div');
                    div.className = `chat-channel-item ${currentActiveChannelId === t.id ? 'active' : ''}`;
                    div.innerText = `#${t.name}`;
                    div.onclick = () => selectChatChannel(t.id);
                    channelsDiv.appendChild(div);
                });
            });
        }

        function selectChatChannel(channelId) {
            currentActiveChannelId = channelId;
            document.querySelectorAll('.chat-channel-item').forEach(el => el.classList.remove('active'));
            fetchChatChannels();
            document.getElementById('chat-input-msg').disabled = false;
            document.getElementById('chat-send-btn').disabled = false;
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML = '<p class="has-text-grey">Pobieranie historii...</p>';
            fetch(`/api/chat/history/${channelId}`).then(res => res.json()).then(messages => {
                messagesDiv.innerHTML = '';
                messages.forEach(msg => appendMessageDOM(msg));
            });
        }

        function appendMessageDOM(msg) {
            const messagesDiv = document.getElementById('chat-messages');
            const row = document.createElement('div');
            row.className = `chat-msg-row ${msg.is_bot ? 'bot' : 'user'}`;
            row.innerHTML = `<div class="chat-msg-author">${msg.author}</div><div>${msg.content}</div><div class="chat-msg-time">${msg.time}</div>`;
            messagesDiv.appendChild(row);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function sendWebMessage() {
            const input = document.getElementById('chat-input-msg');
            const content = input.value.trim();
            if(!content || !currentActiveChannelId) return;
            fetch('/api/chat/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ channel_id: currentActiveChannelId, message: content })
            }).then(() => { input.value = ''; });
        }

        function fetchUsers() {
            const listDiv = document.getElementById('user-list');
            fetch('/api/users').then(res => res.json()).then(data => {
                listDiv.innerHTML = '';
                data.forEach(u => {
                    const div = document.createElement('div');
                    div.className = `user-list-item ${selectedUserId === u.id ? 'active' : ''}`;
                    div.innerHTML = `<img src="${u.avatar}" alt="av"> <span>${u.name}</span>`;
                    div.onclick = () => selectUser(u.id);
                    listDiv.appendChild(div);
                });
            });
        }

        function selectUser(userId) {
            selectedUserId = userId;
            const profileDiv = document.getElementById('user-profile');
            profileDiv.innerHTML = '<p class="has-text-grey">Pobieranie profilu...</p>';
            fetch(`/api/users/${userId}`).then(res => res.json()).then(u => {
                if(u.error) { profileDiv.innerHTML = `<p class='has-text-danger'>${u.error}</p>`; return; }
                
                let rolesHtml = u.roles.map(r => `<span class="role-tag">${r}</span>`).join('');
                profileDiv.innerHTML = `
                    <div class="has-text-centered mb-4">
                        <img src="${u.avatar}" style="width:96px; height:96px; border-radius:50%; border:2px solid #5865f2;">
                        <h3 class="title is-4 has-text-white mt-2">${u.name}</h3>
                        <p class="is-size-7 has-text-grey">ID: ${u.id}</p>
                    </div>
                    <hr style="background-color:rgba(255,255,255,0.08);">
                    <p class="mb-2">📅 **Konto utworzone:** ${u.created_at}</p>
                    <p class="mb-4">📥 **Dołączył na serwer:** ${u.joined_at}</p>
                    <p class="label has-text-grey mb-1">Posiadane Rangi:</p>
                    <div class="mb-5">${rolesHtml || '<span class="has-text-grey-light">Brak specjalnych rang</span>'}</div>
                    
                    <div class="box" style="background:rgba(0,0,0,0.2); border:1px solid rgba(255,255,255,0.05);">
                        <p class="label has-text-white mb-2">⚡ Zarządzanie Rangami</p>
                        <div class="field has-addons">
                            <div class="control is-expanded"><input id="role-input" class="input custom-input" type="text" placeholder="Nazwa roli (np. VIP)"></div>
                            <div class="control"><button class="button btn-glow" onclick="modifyUserRole('add')">Dodaj</button></div>
                            <div class="control"><button class="button btn-danger-glow" onclick="modifyUserRole('remove')">Zabierz</button></div>
                        </div>
                    </div>
                `;
            });
        }

        function modifyUserRole(action) {
            const roleName = document.getElementById('role-input').value.trim();
            if(!roleName || !selectedUserId) return;
            fetch('/api/users/modify-role', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ user_id: selectedUserId, action: action, role_name: roleName })
            }).then(res => res.json()).then(data => {
                if(data.success) { selectUser(selectedUserId); } else { alert("Błąd: " + data.error); }
            });
        }

        function fetchArchive() {
            const archiveDiv = document.getElementById('archive-list');
            fetch('/api/archive').then(res => res.json()).then(data => {
                archiveDiv.innerHTML = '';
                if(data.length === 0) { archiveDiv.innerHTML = '<p class="has-text-grey">Archiwum jest puste.</p>'; return; }
                data.forEach((item, index) => {
                    const div = document.createElement('div');
                    div.className = 'archive-item';
                    div.innerHTML = `
                        <div>
                            <strong style="color:#fff;">#${item.channel_name}</strong> - <span>Ocena: ${'⭐'.repeat(item.rating)} (${item.rating}/5)</span><br>
                            <small class="has-text-grey">Zamknięty przez: ${item.closed_by} | Data: ${item.closed_at}</small>
                        </div>
                        <button class="button is-small btn-glow" onclick="viewTranscript(${index})">Zobacz transkrypcję</button>
                    `;
                    archiveDiv.appendChild(div);
                });
            });
        }

        function viewTranscript(index) {
            fetch('/api/archive').then(res => res.json()).then(data => {
                const item = data[index];
                const messagesDiv = document.getElementById('chat-messages');
                // Przełączamy widok na czat i renderujemy transkrypcję archiwalną
                switchTab({ currentTarget: document.querySelector("a[onclick*='chat-tab']") }, 'chat-tab');
                
                document.getElementById('chat-input-msg').disabled = true;
                document.getElementById('chat-send-btn').disabled = true;
                
                messagesDiv.innerHTML = `<div class="has-text-centered has-text-warning mb-3">📜 WYŚWIETLASZ ARCHIWUM TICKETU #${item.channel_name} (Temat: ${item.subject})</div>`;
                item.messages.forEach(msg => {
                    const row = document.createElement('div');
                    row.className = `chat-msg-row ${msg.is_bot ? 'bot' : 'user'}`;
                    row.innerHTML = `<div class="chat-msg-author">${msg.author}</div><div>${msg.content}</div><div class="chat-msg-time">${msg.time}</div>`;
                    messagesDiv.appendChild(row);
                });
            });
        }

        const eventSource = new EventSource('/api/chat/stream');
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if(currentActiveChannelId && data.channel_id === currentActiveChannelId.toString()) {
                appendMessageDOM(data);
            }
        };

        setInterval(() => { 
            if (document.getElementById('tickets-tab').classList.contains('is-active')) fetchTickets(); 
            if (document.getElementById('chat-tab').classList.contains('is-active') && !document.getElementById('chat-input-msg').disabled) fetchChatChannels();
        }, 8000);
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Zaloguj</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">{{ SHARED_STYLE | safe }}</head>
<body style="display: flex; align-items: center; min-height: 100vh;"><div class="container"><div class="box glass-box p-6" style="max-width: 420px; margin: 0 auto;"><h1 class="title is-3 glow-text has-text-centered mb-5">🔒 Panel Logowania</h1><form method="POST" action="/login"><div class="field mb-5"><input class="input custom-input" type="password" name="password" required placeholder="Hasło"></div><button type="submit" class="button btn-glow is-fullwidth py-4">Zaloguj</button></form></div></div></body>
</html>
"""

# ===============================
# 🌐 TRASY FLASK (ZAPLECZE WWW)
# ===============================

@app.route('/')
def home():
    if not session.get('logged_in'): return render_template_string(LOGIN_TEMPLATE, SHARED_STYLE=SHARED_STYLE)
    current_status = bot_instance.activity.name if bot_instance and bot_instance.activity else ""
    return render_template_string(HTML_TEMPLATE, SHARED_STYLE=SHARED_STYLE, current_status=current_status)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == DASHBOARD_PASSWORD:
        session['logged_in'] = True
        return redirect('/')
    return render_template_string(LOGIN_TEMPLATE, SHARED_STYLE=SHARED_STYLE)

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

@app.route('/update-status', methods=['POST'])
def update_status():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    asyncio.run_coroutine_threadsafe(bot_instance.change_presence(activity=discord.Game(name=request.form.get('status_text', ''))), bot_instance.loop)
    return redirect('/')

@app.route('/api/tickets')
def api_tickets():
    if not session.get('logged_in') or not bot_instance: return jsonify([])
    return jsonify([{"id": str(c.id), "name": c.name} for g in bot_instance.guilds for c in g.text_channels if c.name.startswith("ticket-")])

@app.route('/api/chat/history/<int:channel_id>')
def api_chat_history(channel_id):
    if not session.get('logged_in') or not bot_instance: return jsonify([])
    channel = bot_instance.get_channel(channel_id)
    if not channel: return jsonify([])
    future = asyncio.run_coroutine_threadsafe(channel.history(limit=50, oldest_first=False).flatten(), bot_instance.loop)
    try:
        messages = future.result()
        messages.reverse()
        return jsonify([{"author": m.author.name, "content": m.content, "is_bot": m.author.bot, "time": m.created_at.strftime('%H:%M')} for m in messages])
    except: return jsonify([])

@app.route('/api/chat/send', methods=['POST'])
def api_chat_send():
    if not session.get('logged_in') or not bot_instance: return jsonify({"success": False})
    data = request.json
    channel = bot_instance.get_channel(int(data.get('channel_id')))
    if channel: asyncio.run_coroutine_threadsafe(channel.send(data.get('message')), bot_instance.loop)
    return jsonify({"success": True})

@app.route('/api/chat/stream')
def chat_stream():
    def event_stream():
        q = asyncio.Queue()
        web_listeners.append(q)
        try:
            while True:
                future = asyncio.run_coroutine_threadsafe(q.get(), bot_instance.loop)
                msg_data = future.result()
                yield f"data: {json.dumps(msg_data)}\n\n"
        except GeneratorExit: web_listeners.remove(q)
    return Response(event_stream(), mimetype="text/event-stream")

# NOWE ENDPOINTY DLA BAZY UŻYTKOWNIKÓW i ARCHIWUM
@app.route('/api/users')
def api_users():
    if not session.get('logged_in') or not bot_instance: return jsonify([])
    users_list = []
    for guild in bot_instance.guilds:
        for m in guild.members:
            if not m.bot:
                users_list.append({
                    "id": str(m.id),
                    "name": m.name,
                    "avatar": str(m.display_avatar.url)
                })
    return jsonify(users_list)

@app.route('/api/users/<int:user_id>')
def api_user_details(user_id):
    if not session.get('logged_in') or not bot_instance: return jsonify({"error": "Brak autoryzacji"})
    for guild in bot_instance.guilds:
        m = guild.get_member(user_id)
        if m:
            return jsonify({
                "id": str(m.id),
                "name": m.name,
                "avatar": str(m.display_avatar.url),
                "created_at": m.created_at.strftime('%Y-%m-%d %H:%M'),
                "joined_at": m.joined_at.strftime('%Y-%m-%d %H:%M') if m.joined_at else "Nieznana",
                "roles": [r.name for r in m.roles if r.name != "@everyone"]
            })
    return jsonify({"error": "Nie znaleziono użytkownika na serwerach"})

@app.route('/api/users/modify-role', methods=['POST'])
def api_modify_role():
    if not session.get('logged_in') or not bot_instance: return jsonify({"success": False, "error": "Brak sesji"})
    data = request.json
    user_id = int(data.get('user_id'))
    action = data.get('action')
    role_name = data.get('role_name')

    for guild in bot_instance.guilds:
        m = guild.get_member(user_id)
        role = utils.get(guild.roles, name=role_name)
        if m and role:
            if action == 'add':
                asyncio.run_coroutine_threadsafe(m.add_roles(role), bot_instance.loop)
            elif action == 'remove':
                asyncio.run_coroutine_threadsafe(m.remove_roles(role), bot_instance.loop)
            return jsonify({"success": True})
    return jsonify({"success": False, "error": "Nie znaleziono użytkownika lub roli o tej nazwie"})

@app.route('/api/archive')
def api_get_archive():
    if not session.get('logged_in'): return jsonify([])
    return jsonify(load_archive())

@app.route('/close-ticket-dash', methods=['POST'])
def close_ticket_dash():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    ch_id = request.form.get('channel_id')
    if ch_id and ch_id.isdigit():
        asyncio.run_coroutine_threadsafe(trigger_ticket_close_flow(int(ch_id)), bot_instance.loop)
    return redirect('/')

@app.route('/create-channel', methods=['POST'])
def create_channel():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    asyncio.run_coroutine_threadsafe(create_channel_async(request.form.get('channel_name', ''), request.form.get('channel_type', 'text')), bot_instance.loop)
    return redirect('/')

# ===============================
# ⛓️ ASYNCHRONICZNE POMOCNIKI BOTA
# ===============================

async def trigger_ticket_close_flow(channel_id: int):
    channel = bot_instance.get_channel(channel_id) or await bot_instance.fetch_channel(channel_id)
    if channel:
        await channel.send("⚠️ Zdalne żądanie zamknięcia z panelu WWW. Wywołuję ankietę satysfakcji.")
        await initiate_survey(channel)

async def create_channel_async(name: str, channel_type: str):
    for guild in bot_instance.guilds:
        if channel_type == "text": await guild.create_text_channel(name=name)
        elif channel_type == "voice": await guild.create_voice_channel(name=name)
        break

def keep_alive():
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))))
    t.daemon = True
    t.start()

# ===============================
# 📊 NOWY SYSTEM LOKALNEGO ARCHIWIZOWANIA WWW
# ===============================

async def save_ticket_to_web_archive(channel_id: int, closing_user, rating: int, guild):
    target_channel = guild.get_channel(channel_id)
    if not target_channel: return

    data = ticket_data_cache.get(channel_id, {
        "subject": "Formularz ręczny / brak opisu",
        "creator_mention": "Nieznany"
    })

    messages_list = []
    try:
        async for msg in target_channel.history(limit=600, oldest_first=True):
            messages_list.append({
                "author": msg.author.name,
                "content": msg.content,
                "is_bot": msg.author.bot,
                "time": msg.created_at.strftime('%H:%M')
            })
    except: pass

    # Konstruowanie wpisu do bazy JSON na stronie
    archive_entry = {
        "channel_name": target_channel.name,
        "subject": data.get('subject'),
        "closed_by": closing_user.name,
        "rating": rating,
        "closed_at": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "messages": messages_list
    }
    
    save_to_archive(archive_entry)
    if channel_id in ticket_data_cache: del ticket_data_cache[channel_id]

# ===============================
# 📊 INTERAKTYWNA ANKIETA SATYSFAKCJI
# ===============================

class TicketSurveyView(View):
    def __init__(self): super().__init__(timeout=None)

    async def handle_rating(self, interaction: discord.Interaction, rating: int):
        await interaction.response.defer()
        channel_id = interaction.channel_id
        closing_user = interaction.user
        guild = interaction.guild

        if guild:
            await save_ticket_to_web_archive(channel_id, closing_user, rating, guild)

        for child in self.children: child.disabled = True
        try: await interaction.message.edit(content=f"⭐ Dziękujemy za ocenę: **{rating}/5**! Zapisano w archiwum WWW.", view=self)
        except: pass
        
        await asyncio.sleep(3)
        try:
            if guild:
                tc = guild.get_channel(channel_id)
                if tc: await tc.delete()
        except: pass

    @discord.ui.button(label="1 ⭐", style=discord.ButtonStyle.secondary, custom_id="rate_1")
    async def rate_1(self, interaction: discord.Interaction, button: Button): await self.handle_rating(interaction, 1)

    @discord.ui.button(label="2 ⭐", style=discord.ButtonStyle.secondary, custom_id="rate_2")
    async def rate_2(self, interaction: discord.Interaction, button: Button): await self.handle_rating(interaction, 2)

    @discord.ui.button(label="3 ⭐", style=discord.ButtonStyle.secondary, custom_id="rate_3")
    async def rate_3(self, interaction: discord.Interaction, button: Button): await self.handle_rating(interaction, 3)

    @discord.ui.button(label="4 ⭐", style=discord.ButtonStyle.secondary, custom_id="rate_4")
    async def rate_4(self, interaction: discord.Interaction, button: Button): await self.handle_rating(interaction, 4)

    @discord.ui.button(label="5 ⭐", style=discord.ButtonStyle.success, custom_id="rate_5")
    async def rate_5(self, interaction: discord.Interaction, button: Button): await self.handle_rating(interaction, 5)

async def initiate_survey(channel):
    embed = Embed(
        title="📊 Zamknięcie zgłoszenia",
        description="Oceń pracę naszej administracji. Po kliknięciu transkrypcja zostanie natychmiast przeniesiona do bazy WWW.",
        color=0xffb900
    )
    await channel.send(embed=embed, view=TicketSurveyView())

# ===============================
# 📝 MODALE I WIDOKI DISCORDA
# ===============================

class TicketCreateModal(Modal):
    def __init__(self):
        super().__init__(title="Formularz Zgłoszenia")
        self.subject = TextInput(label="Temat zgłoszenia", placeholder="np. Błąd serwera...", required=True)
        self.description = TextInput(label="Opis problemu", style=discord.TextStyle.paragraph, placeholder="Napisz coś więcej...", required=True)
        self.add_item(self.subject)
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        channel_name = f"ticket-{member.name.lower()}".replace(" ", "-")
        
        if utils.get(guild.text_channels, name=channel_name):
            await interaction.response.send_message("❌ Masz już otwarty ticket!", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        
        ticket_data_cache[ticket_channel.id] = {
            "subject": self.subject.value,
            "description": self.description.value,
            "creator_mention": member.mention
        }

        embed = Embed(title="🎫 Nowy Ticket", color=0x5865f2)
        embed.add_field(name="Temat", value=self.subject.value)
        embed.add_field(name="Opis", value=self.description.value, inline=False)
        await ticket_channel.send(embed=embed, view=TicketActionView())
        await interaction.response.send_message(f"✅ Utworzono kanał {ticket_channel.mention}", ephemeral=True)

class TicketActionView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Zamknij", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Uruchamiam procedurę archiwizacji...", ephemeral=True)
        await initiate_survey(interaction.channel)

class TicketSetupView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Otwórz zgłoszenie", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(TicketCreateModal())

# ===============================
# 🤖 URUCHOMIENIE BOTA
# ===============================

intents = Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def setup_hook():
    global bot_instance
    bot_instance = bot
    bot.add_view(TicketSetupView())
    bot.add_view(TicketActionView())
    bot.add_view(TicketSurveyView())

@bot.event
async def on_ready(): print(f'🤖 System załadowany. Silnik WWW i Bot działają wspólnie.')

@bot.event
async def on_message(message):
    if message.author.bot and message.author != bot.user: return
    if message.channel.name and message.channel.name.startswith("ticket-"):
        payload = {
            "channel_id": str(message.channel.id),
            "author": message.author.name,
            "content": message.content,
            "is_bot": message.author.bot,
            "time": datetime.now().strftime('%H:%M')
        }
        for listener in web_listeners:
            bot.loop.create_task(listener.put(payload))
    await bot.process_commands(message)

@bot.command(name="ticket")
@commands.has_permissions(administrator=True)
async def send_ticket_panel(ctx):
    embed = Embed(title="🎫 Panel Wsparcia", description="Kliknij przycisk poniżej, aby skontaktować się z ekipą serwera.", color=0x2ed573)
    await ctx.send(embed=embed, view=TicketSetupView())
    await ctx.message.delete()

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN: bot.run(TOKEN)
