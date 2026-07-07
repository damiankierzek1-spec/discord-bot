import discord
from discord.ext import commands
from discord import Intents, utils, Embed, File
from discord.ui import Button, View, Modal, TextInput
import os
from flask import Flask, render_template_string, request, redirect, session, jsonify, Response
from threading import Thread
import asyncio
from datetime import datetime, timedelta
from typing import List
import json
import random
import io
from PIL import Image, ImageDraw, ImageFont

# ===============================
# 🚨 KONFIGURACJA GLOBALNA 🚨
# ===============================

ADMIN_IDS: List[int] = [652507356105539585, 550959315700154368, 590215623259193371]
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PWD", "Kuba123!")
ARCHIVE_FILE = "ticket_archive.json"

app = Flask('')
app.secret_key = os.environ.get("FLASK_SECRET", "super-tajny-klucz-kubusiowo")

bot_instance = None
ticket_data_cache = {}
web_listeners = []
captcha_sessions = {}  # Słownik do przechowywania wygenerowanych kodów użytkowników

def load_archive():
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return []
    return []

def save_whole_archive(archive_data):
    with open(ARCHIVE_FILE, 'w', encoding='utf-8') as f: json.dump(archive_data, f, ensure_ascii=False, indent=4)

def save_to_archive(data):
    archive = load_archive()
    archive.append(data)
    save_whole_archive(archive)

# ===============================
# 🎨 ANiMOWANE I BOGATE STYLE CSS (CYBERPUNK GLOW SYSTEM)
# ===============================

SHARED_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght=300;400;500;600;700&display=swap');
    
    :root {
        --bg-gradient: radial-gradient(circle at 50% 50%, #080512 0%, #020105 100%);
        --primary-glow: #5865f2;
        --accent-neon: #00f2fe;
        --danger-neon: #ff007f;
        --warning-neon: #ffae00;
        --panel-bg: rgba(10, 7, 22, 0.55);
        --border-glow: rgba(88, 101, 242, 0.2);
    }

    body { 
        font-family: 'Space Grotesk', sans-serif; 
        background: var(--bg-gradient);
        color: #e2e8f0; 
        min-height: 100vh; 
        margin: 0;
        overflow-x: hidden;
        position: relative;
    }

    #space-canvas {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        z-index: 0; pointer-events: none;
    }

    .animated-bg {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        z-index: -1;
        background: radial-gradient(circle at 15% 25%, rgba(88, 101, 242, 0.15) 0%, transparent 45%),
                    radial-gradient(circle at 85% 75%, rgba(0, 242, 254, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 50% 50%, rgba(255, 0, 127, 0.05) 0%, transparent 40%);
        filter: blur(80px);
        animation: pulseBackground 20s ease-in-out infinite alternate;
    }

    @keyframes pulseBackground {
        0% { transform: scale(1) translate(0, 0); }
        100% { transform: scale(1.1) translate(10px, -10px); }
    }

    .dashboard-container { display: flex; min-height: 100vh; position: relative; z-index: 1; }
    
    .sidebar { 
        width: 280px; 
        background: rgba(8, 5, 18, 0.75); 
        border-right: 1px solid var(--border-glow); 
        backdrop-filter: blur(30px); 
        padding: 2.5rem 1.5rem; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-between;
        box-shadow: 8px 0 35px rgba(0,0,0,0.6);
        z-index: 2;
    }

    .main-content { flex: 1; padding: 3rem; overflow-y: auto; height: 100vh; position: relative; z-index: 1; }

    .menu-list a { 
        color: #8a8da4; 
        padding: 0.9rem 1.2rem; 
        border-radius: 12px; 
        margin-bottom: 0.6rem; 
        display: flex; 
        align-items: center; 
        gap: 14px; 
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
        font-weight: 500;
        border: 1px solid transparent;
    }
    .menu-list a:hover {
        color: #fff;
        background: rgba(255, 255, 255, 0.04);
        transform: translateX(6px);
        border-color: rgba(88, 101, 242, 0.2);
        box-shadow: 0 0 15px rgba(88, 101, 242, 0.1);
    }
    .menu-list a.is-active { 
        background: linear-gradient(90deg, rgba(88, 101, 242, 0.25) 0%, rgba(88, 101, 242, 0.02) 100%); 
        color: #fff; 
        border-left: 4px solid var(--primary-glow);
        padding-left: 14px;
        text-shadow: 0 0 15px rgba(88, 101, 242, 0.6);
        border-color: rgba(88, 101, 242, 0.3);
    }

    .glass-box { 
        background: var(--panel-bg); 
        border: 1px solid var(--border-glow); 
        border-radius: 20px; 
        backdrop-filter: blur(20px); 
        box-shadow: 0 20px 45px rgba(0, 0, 0, 0.5);
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
    }
    .glass-box:hover {
        border-color: rgba(88, 101, 242, 0.4);
        box-shadow: 0 25px 55px rgba(88, 101, 242, 0.15);
        transform: translateY(-3px);
    }

    .glow-text { 
        color: #fff; 
        text-shadow: 0 0 15px rgba(88, 101, 242, 0.8), 0 0 30px rgba(88, 101, 242, 0.3); 
    }

    .btn-glow { 
        background: linear-gradient(135deg, #6c7fff, #5865f2); 
        color: white; border: none; font-weight: 600; border-radius: 10px; 
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); 
        box-shadow: 0 4px 20px rgba(88, 101, 242, 0.4);
    }
    .btn-glow:hover { 
        background: linear-gradient(135deg, #5865f2, #4752c4); 
        transform: translateY(-2px); 
        box-shadow: 0 6px 25px rgba(88, 101, 242, 0.7); 
        color: white; 
    }

    .btn-danger-glow { 
        background: linear-gradient(135deg, #ff4757, #ff0055); 
        color: white; border: none; font-weight: 600; border-radius: 10px; transition: all 0.3s ease; 
        box-shadow: 0 4px 15px rgba(255, 0, 85, 0.3);
    }
    .btn-danger-glow:hover { transform: translateY(-2px); box-shadow: 0 6px 25px rgba(255, 0, 85, 0.6); }

    .btn-warning-glow { 
        background: linear-gradient(135deg, #ffa502, #ff7f50); 
        color: white; border: none; font-weight: 600; border-radius: 10px; transition: all 0.3s ease; 
        box-shadow: 0 4px 15px rgba(255, 165, 2, 0.3);
    }
    .btn-warning-glow:hover { transform: translateY(-2px); box-shadow: 0 6px 25px rgba(255, 165, 2, 0.6); }

    .custom-input, .custom-select select { 
        background: rgba(5, 3, 10, 0.6) !important; 
        border: 1px solid rgba(255, 255, 255, 0.08) !important; 
        color: #fff !important; 
        border-radius: 10px !important; 
        transition: all 0.3s ease;
    }
    .custom-input:focus, .custom-select select:focus { 
        border-color: var(--primary-glow) !important; 
        box-shadow: 0 0 15px rgba(88, 101, 242, 0.3) !important; 
    }

    .tab-content { display: none; }
    .tab-content.is-active { 
        display: block; 
        animation: cyberSlideIn 0.5s cubic-bezier(0.19, 1, 0.22, 1) forwards; 
    }

    @keyframes cyberSlideIn { 
        from { opacity: 0; transform: translateY(25px) scale(0.97); filter: blur(6px); } 
        to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); } 
    }

    .live-pulse-dot {
        width: 10px; height: 10px; background: #00ffa3; border-radius: 50%; display: inline-block;
        box-shadow: 0 0 10px #00ffa3, 0 0 20px #00ffa3;
        animation: pulseDot 1.8s infinite;
        margin-right: 8px;
    }
    @keyframes pulseDot {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 255, 163, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(0, 255, 163, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 255, 163, 0); }
    }

    .chat-container { display: flex; height: 650px; gap: 25px; }
    .chat-channels-list { width: 260px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
    
    .chat-channel-item { 
        padding: 14px; border-radius: 12px; cursor: pointer; 
        background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.04);
        transition: all 0.3s ease;
    }
    .chat-channel-item:hover, .chat-channel-item.active { 
        background: linear-gradient(135deg, rgba(88,101,242,0.25), rgba(0,242,254,0.05));
        border-color: var(--primary-glow); color: #fff; 
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }

    .chat-window { flex: 1; display: flex; flex-direction: column; height: 100%; }
    .chat-messages { 
        flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; 
        background: rgba(0,0,0,0.3); border-radius: 16px; border: 1px solid rgba(255,255,255,0.04);
        scroll-behavior: smooth;
    }
    
    .chat-msg-row { 
        display: flex; flex-direction: column; max-width: 70%; padding: 10px 15px; 
        border-radius: 14px; animation: msgFadeIn 0.3s ease-out forwards;
    }
    @keyframes msgFadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    
    .chat-msg-row.bot { background: rgba(88, 101, 242, 0.18); border: 1px solid rgba(88, 101, 242, 0.3); align-self: flex-end; border-bottom-right-radius: 2px; }
    .chat-msg-row.user { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); align-self: flex-start; border-bottom-left-radius: 2px; }
    .chat-msg-author { font-size: 0.8rem; font-weight: 600; color: #a0aec0; margin-bottom: 4px; }
    .chat-msg-time { font-size: 0.65rem; color: #5a6578; align-self: flex-end; margin-top: 6px; }

    .user-split { display: flex; gap: 25px; height: 700px; }
    .user-list-side { width: 320px; display: flex; flex-direction: column; gap: 12px; }
    .user-scroll-area { flex: 1; overflow-y: auto; background: rgba(0,0,0,0.2); padding: 12px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.04); }
    
    .user-list-item { 
        display: flex; align-items: center; gap: 12px; padding: 10px; border-radius: 10px; 
        cursor: pointer; margin-bottom: 8px; background: rgba(255,255,255,0.01); 
        border: 1px solid transparent; transition: all 0.25s ease; 
    }
    .user-list-item:hover, .user-list-item.active { 
        background: rgba(88, 101, 242, 0.15); border-color: rgba(88, 101, 242, 0.3); 
        color: #fff; transform: translateX(4px);
    }
    .user-list-item img { width: 36px; height: 36px; border-radius: 50%; box-shadow: 0 0 10px rgba(0,0,0,0.5); }
    .user-profile-side { flex: 1; background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.04); padding: 30px; border-radius: 20px; overflow-y: auto; }
    
    .role-tag { 
        display: inline-block; background: rgba(88,101,242,0.12); border: 1px solid rgba(88,101,242,0.4); 
        color: #babcff; padding: 3px 10px; border-radius: 6px; font-size: 0.78rem; margin: 4px; 
        transition: all 0.2s ease;
    }
    .role-tag:hover { background: rgba(88,101,242,0.3); transform: scale(1.05); }

    .ticket-badge, .archive-item { 
        background: rgba(255, 255, 255, 0.01); border: 1px solid rgba(255, 255, 255, 0.04); 
        padding: 16px 24px; border-radius: 14px; margin-bottom: 14px; 
        display: flex; justify-content: space-between; align-items: center;
        transition: all 0.3s ease;
    }
</style>
"""

# ===============================
# 📄 MATRYCA TEMPLATÓW HTML WWW
# ===============================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubusiowo - Panel VIP</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    {{ SHARED_STYLE | safe }}
</head>
<body>
    <div class="animated-bg"></div>
    <canvas id="space-canvas"></canvas>

    <div class="dashboard-container">
        <aside class="sidebar">
            <div>
                <div class="has-text-centered mb-6">
                    <h1 class="title is-4 glow-text mb-2" style="letter-spacing: 2px;">🎮 KUBUSIOWO</h1>
                    <div class="is-flex is-align-items-center is-justify-content-center">
                        <span class="live-pulse-dot"></span>
                        <p class="is-size-7 has-text-grey-light font-weight-bold">LIVE CONSOLE ACTIVE</p>
                    </div>
                </div>
                <ul class="menu-list">
                    <li><a href="#" class="is-active" onmouseenter="playHoverSound()" onclick="switchTab(event, 'status-tab')">⚙️ Status bota</a></li>
                    <li><a href="#" onmouseenter="playHoverSound()" onclick="switchTab(event, 'management-tab')">🛠️ Stwórz Kanał</a></li>
                    <li><a href="#" onmouseenter="playHoverSound()" onclick="switchTab(event, 'users-tab')">👥 Baza Użytkowników</a></li>
                    <li><a href="#" onmouseenter="playHoverSound()" onclick="switchTab(event, 'tickets-tab')">🎫 Aktywne Tickety</a></li>
                    <li><a href="#" onmouseenter="playHoverSound()" onclick="switchTab(event, 'chat-tab')">💬 Czat Ticketów</a></li>
                    <li><a href="#" onmouseenter="playHoverSound()" onclick="switchTab(event, 'archive-tab')">📜 Archiwum Ticketów</a></li>
                </ul>
            </div>
            <div><a href="/logout" class="button btn-danger-glow is-fullwidth py-4" onmouseenter="playHoverSound()" onclick="playClickSound()">Wyloguj system</a></div>
        </aside>

        <main class="main-content">
            <div id="status-tab" class="tab-content is-active">
                <div class="box glass-box p-6" style="max-width: 600px;">
                    <h2 class="title is-3 has-text-white mb-4">Ustawienia Aktywności Bota</h2>
                    <form method="POST" action="/update-status" onclick="playClickSound()">
                        <div class="field mb-5">
                            <label class="label has-text-grey-light is-size-7 mb-2">Treść statusu gry (Playing...)</label>
                            <input class="input custom-input py-4" type="text" name="status_text" value="{{ current_status }}">
                        </div>
                        <button type="submit" class="button btn-glow px-6 py-4">Zaktualizuj status</button>
                    </form>
                </div>
            </div>

            <div id="management-tab" class="tab-content">
                <div class="box glass-box p-5" style="max-width: 500px;">
                    <h3 class="title is-4 has-text-white mb-4">📁 Kreator Kanałów Serwerowych</h3>
                    <form method="POST" action="/create-channel" onclick="playClickSound()">
                        <div class="field mb-3"><input class="input custom-input" type="text" name="channel_name" required placeholder="Nazwa nowego kanału..."></div>
                        <div class="field mb-5"><div class="select is-fullwidth custom-select"><select name="channel_type"><option value="text">Tekstowy</option><option value="voice">Głosowy</option></select></div></div>
                        <button type="submit" class="button btn-glow is-fullwidth py-4">Wygeneruj kanał</button>
                    </form>
                </div>
            </div>

            <div id="users-tab" class="tab-content">
                <div class="box glass-box p-5">
                    <h2 class="title is-4 has-text-white mb-4">👥 Menedżer Użytkowników</h2>
                    <div class="user-split">
                        <div class="user-list-side">
                            <input type="text" id="user-search-input" class="input custom-input mb-3" placeholder="🔍 Wpisz nick, aby szukać..." oninput="filterUsers()">
                            <div id="user-scroll-container" class="user-scroll-area"><p class="has-text-grey is-size-7 p-3">Inicjalizacja rekordów...</p></div>
                        </div>
                        <div id="user-profile" class="user-profile-side">
                            <p class="has-text-grey has-text-centered" style="margin-top: 200px;">Wybierz osobę z bazy danych, aby otworzyć profil cyber-karty.</p>
                        </div>
                    </div>
                </div>
            </div>

            <div id="tickets-tab" class="tab-content">
                <div class="box glass-box p-6">
                    <h2 class="title is-3 has-text-white mb-4">🎫 Aktywne Kanały Ticketów</h2>
                    <div id="tickets-list"><p class="has-text-grey">Wyszukiwanie otwartych zgłoszeń...</p></div>
                </div>
            </div>

            <div id="chat-tab" class="tab-content">
                <div class="box glass-box p-5">
                    <h2 class="title is-4 has-text-white mb-4">💬 Live Chat Matrix (Pisz jako BOT)</h2>
                    <div class="chat-container">
                        <div id="chat-channels" class="chat-channels-list"><p class="has-text-grey is-size-7">Ładowanie kanałów...</p></div>
                        <div class="chat-window">
                            <div id="chat-messages" class="chat-messages">
                                <p class="has-text-grey" style="margin:auto;">Wybierz aktywny strumień kanału z listy obok.</p>
                            </div>
                            <div class="chat-input-area">
                                <input type="text" id="chat-input-msg" class="input custom-input" placeholder="Napisz coś jako bot na kanale..." disabled onkeydown="if(event.key==='Enter') sendWebMessage()">
                                <button id="chat-send-btn" class="button btn-glow" disabled onclick="sendWebMessage()">Wyślij</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div id="archive-tab" class="tab-content">
                <div class="box glass-box p-5">
                    <h2 class="title is-4 has-text-white mb-4">📜 Lokalne Archiwum Transkrypcji Ticketów</h2>
                    <div id="archive-list"><p class="has-text-grey">Parsowanie historii transkrypcji...</p></div>
                </div>
            </div>
        </main>
    </div>

    <script>
        const hoverAudio = new Audio('https://assets.mixkit.co/active_storage/sfx/2568/2568-84.wav');
        const clickAudio = new Audio('https://assets.mixkit.co/active_storage/sfx/2753/2753-84.wav');
        hoverAudio.volume = 0.15; clickAudio.volume = 0.25;

        function playHoverSound() { hoverAudio.currentTime = 0; hoverAudio.play().catch(() => {}); }
        function playClickSound() { clickAudio.currentTime = 0; clickAudio.play().catch(() => {}); }

        const canvas = document.getElementById('space-canvas');
        const ctx = canvas.getContext('2d');
        let stars = []; let meteors = [];

        function resizeCanvas() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
        window.addEventListener('resize', resizeCanvas); resizeCanvas();

        for (let i = 0; i < 120; i++) {
            stars.push({
                x: Math.random() * canvas.width, y: Math.random() * canvas.height,
                size: Math.random() * 1.8, alpha: Math.random(), speed: 0.2 + Math.random() * 0.4
            });
        }

        function spawnMeteor() {
            if (meteors.length < 3 && Math.random() < 0.015) {
                meteors.push({
                    x: Math.random() * canvas.width * 0.8, y: -20,
                    length: 40 + Math.random() * 80, speedX: 4 + Math.random() * 6, speedY: 4 + Math.random() * 6, alpha: 1
                });
            }
        }

        function drawSpace() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            stars.forEach(star => {
                ctx.fillStyle = `rgba(255, 255, 255, ${star.alpha})`;
                ctx.beginPath(); ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2); ctx.fill();
                star.y += star.speed;
                if (star.y > canvas.height) { star.y = 0; star.x = Math.random() * canvas.width; }
            });
            spawnMeteor();
            meteors.forEach((m, idx) => {
                let gradient = ctx.createLinearGradient(m.x, m.y, m.x + m.length, m.y + m.length);
                gradient.addColorStop(0, `rgba(0, 242, 254, ${m.alpha})`);
                gradient.addColorStop(0.5, `rgba(88, 101, 242, ${m.alpha * 0.5})`);
                gradient.addColorStop(1, 'rgba(0,0,0,0)');
                ctx.strokeStyle = gradient; ctx.lineWidth = 2;
                ctx.beginPath(); ctx.moveTo(m.x, m.y); ctx.lineTo(m.x - m.length, m.y - m.length); ctx.stroke();
                m.x += m.speedX; m.y += m.speedY; m.alpha -= 0.012;
                if (m.alpha <= 0 || m.x > canvas.width || m.y > canvas.height) { meteors.splice(idx, 1); }
            });
            requestAnimationFrame(drawSpace);
        }
        drawSpace();

        let currentActiveChannelId = null; let selectedUserId = null; let allUsersData = [];

        function switchTab(evt, tabId) {
            playClickSound();
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
                if (data.length === 0) { listDiv.innerHTML = '<p class="has-text-grey-light">Brak otwartych procesów zgłoszeniowych.</p>'; return; }
                data.forEach(t => {
                    const div = document.createElement('div'); div.className = 'ticket-badge';
                    div.innerHTML = `<div><strong style="color:#fff; font-size:1.1rem;">#${t.name}</strong></div>
                    <form method="POST" action="/close-ticket-dash" style="margin:0;"><input type="hidden" name="channel_id" value="${t.id}"><button type="submit" class="button is-small btn-danger-glow px-5" onclick="playClickSound()">Wymuś Zamknięcie</button></form>`;
                    listDiv.appendChild(div);
                });
            });
        }

        function fetchChatChannels() {
            const channelsDiv = document.getElementById('chat-channels');
            fetch('/api/tickets').then(res => res.json()).then(data => {
                channelsDiv.innerHTML = '';
                if(data.length === 0){ channelsDiv.innerHTML = '<p class="has-text-grey is-size-7">Brak otwartych kanałów.</p>'; return; }
                data.forEach(t => {
                    const div = document.createElement('div');
                    div.className = `chat-channel-item ${currentActiveChannelId === t.id ? 'active' : ''}`;
                    div.innerText = `#${t.name}`; div.onmouseenter = playHoverSound;
                    div.onclick = () => { playClickSound(); selectChatChannel(t.id); };
                    channelsDiv.appendChild(div);
                });
            });
        }

        function selectChatChannel(channelId) {
            currentActiveChannelId = channelId;
            document.getElementById('chat-input-msg').disabled = false;
            document.getElementById('chat-send-btn').disabled = false;
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML = '<p class="has-text-grey">Pobieranie strumienia historii...</p>';
            fetch(`/api/chat/history/${channelId}`).then(res => res.json()).then(messages => {
                messagesDiv.innerHTML = ''; messages.forEach(msg => appendMessageDOM(msg));
            });
        }

        function appendMessageDOM(msg) {
            const messagesDiv = document.getElementById('chat-messages');
            const row = document.createElement('div');
            row.className = `chat-msg-row ${msg.is_bot ? 'bot' : 'user'}`;
            row.innerHTML = `<div class="chat-msg-author">${msg.author}</div><div>${msg.content}</div><div class="chat-msg-time">${msg.time}</div>`;
            messagesDiv.appendChild(row); messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function sendWebMessage() {
            playClickSound();
            const input = document.getElementById('chat-input-msg'); const content = input.value.trim();
            if(!content || !currentActiveChannelId) return;
            fetch('/api/chat/send', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ channel_id: currentActiveChannelId, message: content })
            }).then(() => { input.value = ''; });
        }

        function fetchUsers() { fetch('/api/users').then(res => res.json()).then(data => { allUsersData = data; renderUsersList(allUsersData); }); }

        function renderUsersList(users) {
            const container = document.getElementById('user-scroll-container'); container.innerHTML = '';
            if(users.length === 0) { container.innerHTML = '<p class="has-text-grey is-size-7 p-2">Nie odnaleziono kryteriów.</p>'; return; }
            users.forEach(u => {
                const div = document.createElement('div');
                div.className = `user-list-item ${selectedUserId === u.id ? 'active' : ''}`;
                div.innerHTML = `<img src="${u.avatar}" alt="avatar"> <span>${u.name}</span>`;
                div.onmouseenter = playHoverSound; div.onclick = () => { playClickSound(); selectUser(u.id); };
                container.appendChild(div);
            });
        }

        function filterUsers() {
            const query = document.getElementById('user-search-input').value.toLowerCase().trim();
            const filtered = allUsersData.filter(u => u.name.toLowerCase().includes(query));
            renderUsersList(filtered);
        }

        function selectUser(userId) {
            selectedUserId = userId; const profileDiv = document.getElementById('user-profile');
            profileDiv.innerHTML = '<p class="has-text-grey">Wczytywanie architektury profilu...</p>';
            fetch(`/api/users/${userId}`).then(res => res.json()).then(u => {
                if(u.error) { profileDiv.innerHTML = `<p class='has-text-danger'>${u.error}</p>`; return; }
                let rolesHtml = u.roles.map(r => `<span class="role-tag">${r}</span>`).join('');
                let dropdownOptions = u.server_all_roles.map(rName => `<option value="${rName}">${rName}</option>`).join('');
                profileDiv.innerHTML = `
                    <div class="columns is-mobile is-vcentered mb-4">
                        <div class="column is-narrow"><img src="${u.avatar}" style="width:80px; height:80px; border-radius:50%; border:2px solid var(--primary-glow); box-shadow: 0 0 15px var(--primary-glow);"></div>
                        <div class="column"><h3 class="title is-4 has-text-white mb-1 glow-text">${u.name}</h3><p class="is-size-7 has-text-grey-light">ID: ${u.id}</p></div>
                    </div>
                    <div class="is-size-7 mb-4 p-3" style="background:rgba(0,0,0,0.15); border-radius:10px;">
                        <p>📅 Rejestracja: <span class="has-text-white">${u.created_at}</span></p>
                        <p>📥 Serwer: <span class="has-text-white">${u.joined_at}</span></p>
                    </div>
                    <p class="label has-text-grey-light mb-2 is-size-7">AKTYWNE RANGI:</p>
                    <div class="mb-4">${rolesHtml || '<span class="has-text-grey-light is-size-7">Brak uprawnień</span>'}</div>
                    <div class="box mb-4 p-4" style="background:rgba(0,0,0,0.2); border:1px solid rgba(255,255,255,0.05); border-radius:12px;">
                        <p class="is-size-7 has-text-white mb-2 font-weight-bold">⚡ Przydzielanie / Usuwanie Rang</p>
                        <div class="field has-addons">
                            <div class="control is-expanded"><div class="select is-small is-fullwidth custom-select"><select id="role-dropdown">${dropdownOptions}</select></div></div>
                            <div class="control"><button class="button is-small btn-glow px-4" onclick="modifyUserRole('add')">Nadaj</button></div>
                            <div class="control"><button class="button is-small btn-danger-glow px-4" onclick="modifyUserRole('remove')">Zabierz</button></div>
                        </div>
                    </div>
                    <div class="box p-4" style="background:rgba(255, 0, 127, 0.03); border:1px solid rgba(255, 0, 127, 0.15); border-radius:12px;">
                        <p class="is-size-7 has-text-danger font-weight-bold mb-2">🛡️ KARY I RESTRYKCJE</p>
                        <div class="field mb-3"><input id="mod-reason" type="text" class="input is-small custom-input" placeholder="Powód kary..."></div>
                        <div class="buttons">
                            <button class="button is-small btn-warning-glow" onclick="moderateUser('timeout')">Wycisz (1h)</button>
                            <button class="button is-small btn-danger-glow" onclick="moderateUser('kick')">Wyrzuć</button>
                            <button class="button is-small btn-danger-glow" style="background:linear-gradient(135deg, crimson, #ff0000);" onclick="moderateUser('ban')">Zbanuj</button>
                        </div>
                    </div>`;
            });
        }

        function modifyUserRole(action) {
            playClickSound(); const dropdown = document.getElementById('role-dropdown'); if(!dropdown || !selectedUserId) return;
            fetch('/api/users/modify-role', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ user_id: selectedUserId, action: action, role_name: dropdown.value })
            }).then(res => res.json()).then(data => { if(data.success) selectUser(selectedUserId); });
        }

        function moderateUser(action) {
            playClickSound(); const reasonInput = document.getElementById('mod-reason'); if(!reasonInput || !selectedUserId) return;
            const reason = reasonInput.value.trim() || "Akcja z panelu WWW Cyber-Glow.";
            if(!confirm(`Czy na pewno chcesz wykonać operację ${action.toUpperCase()}?`)) return;
            fetch('/api/users/moderate', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ user_id: selectedUserId, action: action, reason: reason })
            }).then(res => res.json()).then(data => {
                if(data.success) { fetchUsers(); document.getElementById('user-profile').innerHTML = '<p class="has-text-grey has-text-centered" style="margin-top: 200px;">Wybierz osobę z bazy danych, aby otworzyć profil cyber-karty.</p>'; }
            });
        }

        function fetchArchive() {
            const archiveDiv = document.getElementById('archive-list');
            fetch('/api/archive').then(res => res.json()).then(data => {
                archiveDiv.innerHTML = ''; if(data.length === 0) { archiveDiv.innerHTML = '<p class="has-text-grey">Archiwum systemowe jest puste.</p>'; return; }
                data.forEach((item, index) => {
                    const div = document.createElement('div'); div.className = 'archive-item';
                    div.innerHTML = `<div><strong style="color:#fff; font-size:1.05rem;">#${item.channel_name}</strong> - <span>Ocena: ${'⭐'.repeat(item.rating)}</span><br><small class="has-text-grey-light">Zamknął: ${item.closed_by} | ${item.closed_at}</small></div>
                        <div class="buttons"><button class="button is-small btn-glow" onclick="viewTranscript(${index})">Wgląd</button><button class="button is-small btn-danger-glow" onclick="deleteTranscript(${index})">Usuń</button></div>`;
                    archiveDiv.appendChild(div);
                });
            });
        }

        function deleteTranscript(index) {
            playClickSound(); if(!confirm("Usunąć trwale plik transkrypcji?")) return;
            fetch(`/api/archive/delete/${index}`, { method: 'DELETE' }).then(res => res.json()).then(data => { if(data.success) fetchArchive(); });
        }

        function viewTranscript(index) {
            playClickSound(); fetch('/api/archive').then(res => res.json()).then(data => {
                const item = data[index]; const messagesDiv = document.getElementById('chat-messages');
                switchTab({ currentTarget: document.querySelector("a[onclick*='chat-tab']") }, 'chat-tab');
                document.getElementById('chat-input-msg').disabled = true; document.getElementById('chat-send-btn').disabled = true;
                messagesDiv.innerHTML = `<div class="has-text-centered has-text-warning mb-3" style="font-size:0.85rem; letter-spacing:1px;">📜 LOGI ARCHIWALNE PROTOKOŁU #${item.channel_name}</div>`;
                item.messages.forEach(msg => {
                    const row = document.createElement('div'); row.className = `chat-msg-row ${msg.is_bot ? 'bot' : 'user'}`;
                    row.innerHTML = `<div class="chat-msg-author">${msg.author}</div><div>${msg.content}</div><div class="chat-msg-time">${msg.time}</div>`;
                    messagesDiv.appendChild(row);
                });
            });
        }

        const eventSource = new EventSource('/api/chat/stream');
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if(currentActiveChannelId && data.channel_id === currentActiveChannelId.toString()) appendMessageDOM(data);
        };
        setInterval(() => { if (document.getElementById('tickets-tab').classList.contains('is-active')) fetchTickets(); }, 6000);
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Zaloguj</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">{{ SHARED_STYLE | safe }}</head>
<body style="display: flex; align-items: center; min-height: 100vh;"><div class="animated-bg"></div><div class="container">
<div class="box glass-box p-6" style="max-width: 440px; margin: 0 auto;"><h1 class="title is-3 glow-text has-text-centered mb-5" style="letter-spacing:1px;">🔒 SYSTEM AUTORYZACJI</h1>
<form method="POST" action="/login"><div class="field mb-5"><input class="input custom-input py-4" type="password" name="password" required placeholder="Wprowadź klucz dostępu..."></div><button type="submit" class="button btn-glow is-fullwidth py-4">Autoryzuj wejście</button></form>
</div></div></body></html>
"""

# ===============================
# 🌐 TRASY I ZAPLECZE FLASK
# ===============================

@app.route('/')
def home():
    if not session.get('logged_in'): return render_template_string(LOGIN_TEMPLATE, SHARED_STYLE=SHARED_STYLE)
    current_status = bot_instance.activity.name if bot_instance and bot_instance.activity else ""
    return render_template_string(HTML_TEMPLATE, SHARED_STYLE=SHARED_STYLE, current_status=current_status)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == DASHBOARD_PASSWORD: session['logged_in'] = True; return redirect('/')
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
    channel = bot_instance.get_channel(channel_id) or asyncio.run_coroutine_threadsafe(bot_instance.fetch_channel(channel_id), bot_instance.loop).result()
    if not channel: return jsonify([])
    future = asyncio.run_coroutine_threadsafe(channel.history(limit=50, oldest_first=False).flatten(), bot_instance.loop)
    try:
        messages = future.result(); messages.reverse()
        return jsonify([{"author": m.author.name, "content": m.content, "is_bot": m.author.bot, "time": m.created_at.strftime('%H:%M')} for m in messages])
    except: return jsonify([])

@app.route('/api/chat/send', methods=['POST'])
def api_chat_send():
    if not session.get('logged_in') or not bot_instance: return jsonify({"success": False})
    data = request.json; channel = bot_instance.get_channel(int(data.get('channel_id')))
    if channel: asyncio.run_coroutine_threadsafe(channel.send(data.get('message')), bot_instance.loop)
    return jsonify({"success": True})

@app.route('/api/chat/stream')
def chat_stream():
    def event_stream():
        q = asyncio.Queue(); web_listeners.append(q)
        try:
            while True:
                future = asyncio.run_coroutine_threadsafe(q.get(), bot_instance.loop)
                yield f"data: {json.dumps(future.result())}\n\n"
        except GeneratorExit: web_listeners.remove(q)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/api/users')
def api_users():
    if not session.get('logged_in') or not bot_instance: return jsonify([])
    users_list = []
    for guild in bot_instance.guilds:
        for m in guild.members:
            if not m.bot: users_list.append({"id": str(m.id), "name": m.name, "avatar": str(m.display_avatar.url)})
    return jsonify(users_list)

@app.route('/api/users/<int:user_id>')
def api_user_details(user_id):
    if not session.get('logged_in') or not bot_instance: return jsonify({"error": "Brak autoryzacji"})
    for guild in bot_instance.guilds:
        m = guild.get_member(user_id)
        if m:
            all_server_roles = [r.name for r in guild.roles if r.name != "@everyone" and not r.managed]
            return jsonify({
                "id": str(m.id), "name": m.name, "avatar": str(m.display_avatar.url),
                "created_at": m.created_at.strftime('%Y-%m-%d %H:%M'),
                "joined_at": m.joined_at.strftime('%Y-%m-%d %H:%M') if m.joined_at else "Nieznana",
                "roles": [r.name for r in m.roles if r.name != "@everyone"], "server_all_roles": all_server_roles
            })
    return jsonify({"error": "Nie znaleziono rekordu"})

@app.route('/api/users/modify-role', methods=['POST'])
def api_modify_role():
    if not session.get('logged_in') or not bot_instance: return jsonify({"success": False})
    data = request.json; user_id = int(data.get('user_id')); action = data.get('action'); role_name = data.get('role_name')
    for guild in bot_instance.guilds:
        m = guild.get_member(user_id); role = utils.get(guild.roles, name=role_name)
        if m and role:
            if action == 'add': asyncio.run_coroutine_threadsafe(m.add_roles(role), bot_instance.loop)
            elif action == 'remove': asyncio.run_coroutine_threadsafe(m.remove_roles(role), bot_instance.loop)
            return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/api/users/moderate', methods=['POST'])
def api_moderate_user():
    if not session.get('logged_in') or not bot_instance: return jsonify({"success": False})
    data = request.json; user_id = int(data.get('user_id')); action = data.get('action'); reason = data.get('reason', "WWW Panel")
    for guild in bot_instance.guilds:
        m = guild.get_member(user_id)
        if m:
            try:
                if action == 'timeout': asyncio.run_coroutine_threadsafe(m.timeout(timedelta(hours=1), reason=reason), bot_instance.loop)
                elif action == 'kick': asyncio.run_coroutine_threadsafe(m.kick(reason=reason), bot_instance.loop)
                elif action == 'ban': asyncio.run_coroutine_threadsafe(guild.ban(m, reason=reason), bot_instance.loop)
                return jsonify({"success": True})
            except Exception as e: return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": False})

@app.route('/api/archive')
def api_get_archive():
    if not session.get('logged_in'): return jsonify([])
    return jsonify(load_archive())

@app.route('/api/archive/delete/<int:index>', methods=['DELETE'])
def api_delete_archive(index):
    if not session.get('logged_in'): return jsonify({"success": False})
    archive = load_archive()
    if 0 <= index < len(archive): archive.pop(index); save_whole_archive(archive); return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/close-ticket-dash', methods=['POST'])
def close_ticket_dash():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    ch_id = request.form.get('channel_id')
    if ch_id and ch_id.isdigit(): asyncio.run_coroutine_threadsafe(trigger_ticket_close_flow(int(ch_id)), bot_instance.loop)
    return redirect('/')

@app.route('/create-channel', methods=['POST'])
def create_channel():
    if not session.get('logged_in') or not bot_instance: return redirect('/')
    asyncio.run_coroutine_threadsafe(create_channel_async(request.form.get('channel_name', ''), request.form.get('channel_type', 'text')), bot_instance.loop)
    return redirect('/')

# ===============================
# ⛓️ ASYNCHRONICZNE LOGIKI BOTA DISCORD
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
    t.daemon = True; t.start()

async def save_ticket_to_web_archive(channel_id: int, closing_user, rating: int, guild):
    target_channel = guild.get_channel(channel_id)
    if not target_channel: return
    data = ticket_data_cache.get(channel_id, {"subject": "Brak opisu"})
    messages_list = []
    try:
        async for msg in target_channel.history(limit=600, oldest_first=True):
            messages_list.append({"author": msg.author.name, "content": msg.content, "is_bot": msg.author.bot, "time": msg.created_at.strftime('%H:%M')})
    except: pass
    archive_entry = {
        "channel_name": target_channel.name, "subject": data.get('subject'), "closed_by": closing_user.name,
        "rating": rating, "closed_at": datetime.now().strftime('%Y-%m-%d %H:%M'), "messages": messages_list
    }
    save_to_archive(archive_entry)
    if channel_id in ticket_data_cache: del ticket_data_cache[channel_id]

# ===============================
# 🧩 GENERATOR CAPTCHA (PIL)
# ===============================

def generate_captcha_image(text: str) -> io.BytesIO:
    # Tworzenie ciemnego, cyberpunkowego tła obrazka
    img = Image.new('RGB', (160, 60), color=(15, 12, 28))
    d = ImageDraw.Draw(img)
    
    # Rysowanie losowych linii zakłócających (anty-bot)
    for _ in range(5):
        d.line([(random.randint(0, 160), random.randint(0, 60)), (random.randint(0, 160), random.randint(0, 60))], fill=(88, 101, 242), width=1)
    
    # Używamy standardowej czcionki wbudowanej, by nie wymagać plików .ttf na dysku
    # Wypisywanie znaków z delikatnym przesunięciem
    for i, char in enumerate(text):
        d.text((15 + i * 35, 15), char, fill=(0, 242, 254))
        
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# ===============================
# 📊 WIDOKI I ANKIETY INTERAKTYWNE
# ===============================

class CaptchaSubmitModal(Modal):
    def __init__(self):
        super().__init__(title="Weryfikacja Konta")
        self.code_input = TextInput(label="Wpisz kod z obrazka CAPTCHA", placeholder="Wprowadź 4 znaki...", required=True, min_length=4, max_length=4)
        self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        correct_code = captcha_sessions.get(user_id)
        
        if not correct_code:
            await interaction.response.send_message("❌ Sesja weryfikacji wygasła. Spróbuj ponownie na serwerze.", ephemeral=True)
            return
            
        if self.code_input.value.upper() == correct_code:
            # Szukamy gildii na której użytkownik się weryfikuje
            for guild in bot_instance.guilds:
                member = guild.get_member(user_id)
                if member:
                    role = utils.get(guild.roles, name="ZWERYFIKOWANY")
                    if not role:
                        # Jeśli ranga nie istnieje, spróbujemy ją stworzyć w locie
                        try: role = await guild.create_role(name="ZWERYFIKOWANY", reason="Automatyczny system weryfikacji.")
                        except: pass
                    
                    if role:
                        await member.add_roles(role)
                        del captcha_sessions[user_id]
                        await interaction.response.send_message("✅ Autoryzacja pomyślna! Otrzymałeś rangę `ZWERYFIKOWANY`.", ephemeral=True)
                        return
            await interaction.response.send_message("❌ Wystąpił błąd podczas dodawania rangi. Skontaktuj się z administratorem.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Błędny kod CAPTCHA! Spróbuj ponownie.", ephemeral=True)

class CaptchaDMView(View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="🔑 Wpisz Kod", style=discord.ButtonStyle.success, custom_id="submit_captcha_btn")
    async def submit_captcha(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(CaptchaSubmitModal())

class VerificationSetupView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔐 Rozpocznij Weryfikację", style=discord.ButtonStyle.primary, custom_id="start_verification_btn")
    async def start_verification(self, interaction: discord.Interaction, button: Button):
        # Sprawdzamy czy użytkownik ma już rangę
        role = utils.get(interaction.user.roles, name="ZWERYFIKOWANY")
        if role:
            await interaction.response.send_message("ℹ️ Jesteś już zweryfikowany na tym serwerze!", ephemeral=True)
            return
            
        await interaction.response.send_message("📩 Sprawdź swoje wiadomości prywatne (DM) – wysłaliśmy tam kod CAPTCHA.", ephemeral=True)
        
        # Generowanie losowego kodu
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # wykluczone mylące znaki typu O, 0, I, 1
        captcha_code = "".join(random.choice(chars) for _ in range(4))
        captcha_sessions[interaction.user.id] = captcha_code
        
        # Generowanie i wysyłka obrazka
        img_buf = generate_captcha_image(captcha_code)
        file = File(fp=img_buf, filename="captcha.png")
        
        embed = Embed(
            title="🔒 Weryfikacja Serwerowa", 
            description="Przepisz kod z poniższego obrazka klikając zielony przycisk.\nWielkość liter nie ma znaczenia.", 
            color=0x5865f2
        )
        embed.set_image(url="attachment://captcha.png")
        
        try:
            await interaction.user.send(embed=embed, file=file, view=CaptchaDMView())
        except discord.Forbidden:
            # Obsługa błędu gdy ktoś ma zablokowane wiadomości prywatne
            pass

# (Wcześniejsze klasy widoków ticketów bez zmian)
class TicketSurveyView(View):
    def __init__(self): super().__init__(timeout=None)
    async def handle_rating(self, interaction: discord.Interaction, rating: int):
        await interaction.response.defer(); channel_id = interaction.channel_id; closing_user = interaction.user; guild = interaction.guild
        if guild: await save_ticket_to_web_archive(channel_id, closing_user, rating, guild)
        for child in self.children: child.disabled = True
        try: await interaction.message.edit(content=f"⭐ Dziękujemy za ocenę: **{rating}/5**!", view=self)
        except: pass
        await asyncio.sleep(2)
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
    embed = Embed(title="📊 Zamknięcie zgłoszenia", description="Oceń pracę naszej administracji. Po kliknięciu transkrypcja trafi do panelu WWW.", color=0xffb900)
    await channel.send(embed=embed, view=TicketSurveyView())

class TicketCreateModal(Modal):
    def __init__(self):
        super().__init__(title="Formularz Zgłoszenia")
        self.subject = TextInput(label="Temat zgłoszenia", placeholder="Np. Błąd konfiguracji...", required=True)
        self.description = TextInput(label="Opis problemu", style=discord.TextStyle.paragraph, placeholder="Opisz dokładnie sytuację...", required=True)
        self.add_item(self.subject); self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild; member = interaction.user; channel_name = f"ticket-{member.name.lower()}".replace(" ", "-")
        if utils.get(guild.text_channels, name=channel_name):
            await interaction.response.send_message("❌ Masz już aktywny kanał wsparcia!", ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        ticket_data_cache[ticket_channel.id] = {"subject": self.subject.value, "description": self.description.value, "creator_mention": member.mention}
        embed = Embed(title="🎫 Zgłoszenie Otwarte", color=0x5865f2)
        embed.add_field(name="Temat", value=self.subject.value)
        embed.add_field(name="Opis", value=self.description.value, inline=False)
        await ticket_channel.send(embed=embed, view=TicketActionView())
        await interaction.response.send_message(f"✅ Utworzono kanał {ticket_channel.mention}", ephemeral=True)

class TicketActionView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Zamknij", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Inicjalizacja archiwum...", ephemeral=True)
        await initiate_survey(interaction.channel)

class TicketSetupView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Otwórz zgłoszenie", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: Button): await interaction.response.send_modal(TicketCreateModal())

# ===============================
# 🤖 STARTER SYSTEMU
# ===============================

intents = Intents.default()
intents.message_content = True; intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def setup_hook():
    global bot_instance; bot_instance = bot
    # Rejestracja widoków w celu zachowania ich działania po restarcie bota
    bot.add_view(TicketSetupView())
    bot.add_view(TicketActionView())
    bot.add_view(TicketSurveyView())
    bot.add_view(VerificationSetupView())

@bot.event
async def on_ready(): print(f'🤖 System Cyber-Glow & CAPTCHA Weryfikacji aktywny.')

@bot.event
async def on_message(message):
    if message.author.bot and message.author != bot.user: return
    if message.channel.name and message.channel.name.startswith("ticket-"):
        payload = {
            "channel_id": str(message.channel.id), "author": message.author.name,
            "content": message.content, "is_bot": message.author.bot, "time": datetime.now().strftime('%H:%M')
        }
        for listener in web_listeners: bot.loop.create_task(listener.put(payload))
    await bot.process_commands(message)

@bot.command(name="ticket")
@commands.has_permissions(administrator=True)
async def send_ticket_panel(ctx):
    embed = Embed(title="🎫 Centrum Wsparcia", description="Kliknij przycisk, aby otworzyć bezpieczne połączenie z administracją.", color=0x2ed573)
    await ctx.send(embed=embed, view=TicketSetupView()); await ctx.message.delete()

# Komenda do postawienia panelu weryfikacyjnego
@bot.command(name="setup-weryfikacja")
@commands.has_permissions(administrator=True)
async def send_verification_panel(ctx):
    embed = Embed(
        title="🔐 SYSTEM WERYFIKACJI", 
        description="Aby uzyskać dostęp do pozostałych sekcji serwera, przejdź proces autoryzacji CAPTCHA.\n\nKliknij przycisk poniżej, aby otrzymać unikalny token dostępu.", 
        color=0x5865f2
    )
    await ctx.send(embed=embed, view=VerificationSetupView())
    await ctx.message.delete()

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN: bot.run(TOKEN)
