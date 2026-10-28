"""
شكون أنا؟ - Who Am I?
نسخة تدعم المجموعات (Groups) والمحادثات الخاصة بالكامل.
المتطلبات: pip install aiohttp
"""
import asyncio
import hashlib
import hmac
import json
import os
import random
import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import parse_qsl, unquote
import aiohttp
from aiohttp import WSMsgType, web

# --- بيانات البوت والمالك ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "9269122102:AAFxKUbT6Bw4_lIfLWVenBDTWQ1M9_fGzMA")
APP_URL = "https://chkon-ana.onrender.com/"
OWNER_USERNAME = "IIlIlIlllIIllIIl"
OWNER_ID = 8684495458
PORT = int(os.getenv("PORT", "8080"))

STATS_FILE = Path(__file__).parent / "stats.json"
USERS_FILE = Path(__file__).parent / "users.json"

ROUNDS = (3, 5, 8, 10)
TIMERS = (30, 45, 60, 90)
MAX_PLAYERS = 12

# ربط كل مجموعة بغرفتها النشطة
GROUP_ROOMS = {}

# بنك الكلمات مع الكلمات المحظورة لنمط Taboo
WORDS_DATA = {
    "celebs": [
        {"word": "الشاب خالد", "taboo": ["دي دي", "مغني", "وهران"]},
        {"word": "زين الدين زيدان", "taboo": ["فرنسا", "ريال مدريد", "كرة"]},
        {"word": "الشاب حسني", "taboo": ["راي", "عاطفي", "مرحوم"]},
        {"word": "عثمان عريوات", "taboo": ["كرنفال في دشرة", "ممثل", "ضحك"]},
        {"word": "صالح أوقروت", "taboo": ["عاشور العاشر", "جمعي فاملي", "كوميديا"]},
        {"word": "لخضر بلومي", "taboo": ["رقم 10", "هدف", "المانيا"]},
        {"word": "سولكينغ", "taboo": ["غناء", "راب", "فرنسا"]}
    ],
    "football": [
        {"word": "رياض محرز", "taboo": ["سيتي", "أهلي", "يسارية"]},
        {"word": "ليونيل ميسي", "taboo": ["أرجنتين", "برشلونة", "كرة ذهبية"]},
        {"word": "كريستيانو رونالدو", "taboo": ["نصر", "برتغال", "ريال مدريد"]},
        {"word": "محمد صلاح", "taboo": ["مصر", "ليفربول", "فخر العرب"]},
        {"word": "إسماعيل بن ناصر", "taboo": ["ميلان", "وسط", "محارب"]},
        {"word": "يوسف بلايلي", "taboo": ["مراوغ", "مولودية", "ترجي"]}
    ],
    "anime": [
        {"word": "ناروتو", "taboo": ["نينجا", "ساسكي", "هوكاجي"]},
        {"word": "لوفي", "taboo": ["قبعة القش", "ون بيس", "مطاط"]},
        {"word": "غوكو", "taboo": ["دراغون بول", "سايان", "كاميهاميها"]},
        {"word": "كونان", "taboo": ["متحري", "تقلص", "سينشي"]},
        {"word": "ليفاي", "taboo": ["هجوم العمالقة", "قائد", "نظافة"]}
    ],
    "food": [
        {"word": "الشخشوخة", "taboo": ["بسكرة", "حار", "مرقة"]},
        {"word": "الكسكسي", "taboo": ["جمعة", "طعام", "خضار"]},
        {"word": "المحجوبة", "taboo": ["بصل", "حار", "فرينة"]},
        {"word": "الكرنتيكا", "taboo": ["حمص", "وهران", "كمون"]},
        {"word": "البوراك", "taboo": ["رمضان", "ديول", "بطاطا"]}
    ],
    "general": [
        {"word": "برج إيفل", "taboo": ["باريس", "فرنسا", "حديد"]},
        {"word": "الأهرامات", "taboo": ["مصر", "فراعنة", "مثلث"]},
        {"word": "الإنترنت", "taboo": ["شبكة", "ويفي", "مواقع"]},
        {"word": "الذكاء الاصطناعي", "taboo": ["روبوت", "حاسوب", "تفكير"]},
        {"word": "السيارة", "taboo": ["عجلات", "سياقة", "محرك"]}
    ]
}

def load_db(path):
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                return {str(x): True for x in data}
        except Exception:
            return {}
    return {}

def save_db(path, data):
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

STATS = load_db(STATS_FILE)
USERS = set(load_db(USERS_FILE).keys())

def update_user_stats(uid, name, add_score=0, won=False):
    s_uid = str(uid)
    if s_uid not in STATS:
        STATS[s_uid] = {"name": name, "score": 0, "wins": 0, "games": 0}
    STATS[s_uid]["name"] = name
    STATS[s_uid]["score"] += add_score
    STATS[s_uid]["games"] += 1
    if won:
        STATS[s_uid]["wins"] += 1
    save_db(STATS_FILE, STATS)

def get_leaderboard_data():
    sorted_players = sorted(
        STATS.items(),
        key=lambda item: (item[1].get("score", 0), item[1].get("wins", 0)),
        reverse=True
    )[:10]
    return [
        {
            "rank": idx + 1,
            "id": uid,
            "name": p.get("name", "لاعب"),
            "score": p.get("score", 0),
            "wins": p.get("wins", 0),
            "games": p.get("games", 0)
        }
        for idx, (uid, p) in enumerate(sorted_players)
    ]

# --- واجهة المستخدم الكاملة ---
HTML_PAGE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="color-scheme" content="dark">
<title>شكون أنا؟</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #090814;
  --bg-subtle: #0f0c22;
  --surface: #14112c;
  --surface-hover: #1c183d;
  --border: rgba(168, 85, 247, 0.2);
  --text: #f8f7ff;
  --text-muted: #948fb3;
  --primary: #9333ea;
  --primary-light: #a855f7;
  --gold: #eab308;
  --success: #10b981;
  --danger: #ef4444;
  --grad-primary: linear-gradient(135deg, #9333ea 0%, #3b82f6 100%);
  --grad-surface: linear-gradient(180deg, rgba(25, 21, 53, 0.85) 0%, rgba(17, 14, 38, 0.95) 100%);
  --radius-lg: 20px;
  --radius-md: 14px;
}
* { box-sizing: border-box; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }
html, body { min-height: 100%; background-color: var(--bg); }
body {
  font-family: "Cairo", "Inter", system-ui, sans-serif;
  font-size: 14px;
  color: var(--text);
  background: radial-gradient(1000px 500px at 50% -120px, rgba(147, 51, 234, 0.22), transparent 75%), var(--bg);
  background-attachment: fixed;
  user-select: none;
  overflow-x: hidden;
}
html[dir="ltr"] body { font-family: "Inter", "Cairo", system-ui, sans-serif; }
.sprite { position: absolute; width: 0; height: 0; overflow: hidden; }
.ic { width: 19px; height: 19px; flex: none; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; display: inline-block; vertical-align: middle; }
.app { max-width: 480px; margin: 0 auto; min-height: 100vh; display: flex; flex-direction: column; padding: 14px; position: relative; }
.top-nav { display: flex; align-items: center; gap: 8px; padding: 6px 0 14px; }
.brand-badge { width: 38px; height: 38px; border-radius: 12px; background: var(--grad-primary); display: grid; place-items: center; color: #fff; }
.grow { flex: 1; }
.nav-actions { display: flex; align-items: center; gap: 6px; }
.status-pill { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 700; padding: 4px 8px; border-radius: 99px; background: var(--surface); border: 1px solid var(--border); color: var(--text-muted); }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--success); }
.status-pill.offline .status-dot { background: var(--danger); }
.icon-btn { width: 36px; height: 36px; border-radius: 11px; border: 1px solid var(--border); background: var(--surface); color: var(--text); display: grid; place-items: center; cursor: pointer; }
.card { background: var(--grad-surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; margin-bottom: 12px; }
.card-title { display: flex; align-items: center; gap: 8px; font-size: 13.5px; font-weight: 700; color: var(--text-muted); margin-bottom: 12px; }
.field { width: 100%; font-family: inherit; font-size: 14px; color: var(--text); background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 12px 14px; outline: none; }
.code-field { text-align: center; letter-spacing: 0.25em; font-family: monospace; font-weight: 800; font-size: 18px; text-transform: uppercase; }
.row { display: flex; gap: 8px; }
.row > * { flex: 1; min-width: 0; }
.btn { width: 100%; display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 0; border-radius: var(--radius-md); padding: 13px 18px; font-family: inherit; font-size: 14.5px; font-weight: 800; color: #fff; background: var(--grad-primary); cursor: pointer; }
.btn-secondary { background: var(--surface-hover); border: 1px solid var(--border); color: var(--text); }
.btn-sm { width: auto; flex: none; padding: 12px 18px; }
.room-code { font-family: monospace; font-size: 36px; font-weight: 900; letter-spacing: 0.3em; text-indent: 0.3em; background: var(--grad-primary); -webkit-background-clip: text; background-clip: text; color: transparent; text-align: center; margin: 10px 0; }
.players-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.player-item { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: var(--radius-md); background: var(--bg-subtle); border: 1px solid var(--border); min-width: 0; }
.avatar-badge { width: 34px; height: 34px; border-radius: 50%; display: grid; place-items: center; font-weight: 800; color: #fff; flex: none; font-size: 13px; }
.player-name { font-weight: 700; font-size: 12.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.taboo-tag { display: inline-block; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: var(--danger); padding: 4px 10px; border-radius: 99px; font-size: 12px; font-weight: 700; margin: 2px; }
.reactions-bar { display: flex; justify-content: center; gap: 10px; margin-top: 10px; padding: 8px; background: var(--bg-subtle); border-radius: var(--radius-md); border: 1px solid var(--border); }
.react-btn { font-size: 20px; background: transparent; border: 0; cursor: pointer; transition: transform 0.15s; }
.react-btn:active { transform: scale(1.3); }
.flying-reaction { position: fixed; bottom: 80px; font-size: 32px; pointer-events: none; animation: flyUp 1.8s ease-out forwards; z-index: 9999; }
@keyframes flyUp { 0% { opacity: 1; transform: translateY(0) scale(0.6); } 100% { opacity: 0; transform: translateY(-380px) scale(1.4); } }
.badge-pill { display: inline-block; font-size: 10.5px; font-weight: 800; padding: 2px 8px; border-radius: 99px; background: rgba(234, 179, 8, 0.15); color: var(--gold); border: 1px solid rgba(234, 179, 8, 0.3); }
.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; padding: 16px; z-index: 999; }
.modal-box { width: 100%; max-width: 420px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; max-height: 85vh; overflow-y: auto; }
.stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 14px; }
.stat-card { background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 12px; text-align: center; }
.stat-val { font-size: 22px; font-weight: 900; color: var(--gold); }
.stat-lbl { font-size: 11px; color: var(--text-muted); font-weight: 700; }
.toast-msg { position: fixed; inset-inline: 0; bottom: 20px; margin: auto; width: max-content; max-width: 90%; background: var(--surface-hover); border: 1px solid var(--border); padding: 10px 16px; border-radius: var(--radius-md); font-weight: 700; opacity: 0; transform: translateY(12px); transition: 0.2s; pointer-events: none; z-index: 1000; }
.toast-msg.show { opacity: 1; transform: translateY(0); }
.hidden { display: none !important; }
.spinner { width: 32px; height: 32px; border-radius: 50%; border: 3px solid var(--border); border-top-color: var(--primary-light); animation: spin 0.8s linear infinite; margin: 0 auto 12px; }
@keyframes spin { to { transform: rotate(360deg); } }
canvas#confettiCanvas { position: fixed; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 9998; }
</style>
</head>
<body>

<canvas id="confettiCanvas"></canvas>

<svg class="sprite" aria-hidden="true">
  <symbol id="i-logo" viewBox="0 0 24 24"><path d="M12 2a8 8 0 0 0-8 8c0 3 2 5.5 5 7.2V19a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-1.8c3-1.7 5-4.2 5-7.2a8 8 0 0 0-8-8z"/><path d="M9 10a3 3 0 0 1 6 0c0 1.5-1.5 2.5-3 3"/><path d="M12 17h.01"/></symbol>
  <symbol id="i-target" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></symbol>
  <symbol id="i-bulb" viewBox="0 0 24 24"><path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V17h5v-1.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3z"/></symbol>
  <symbol id="i-crown" viewBox="0 0 24 24"><path d="M3 18h18M4 14l3-8 5 5 5-5 3 8z"/></symbol>
  <symbol id="i-trophy" viewBox="0 0 24 24"><path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0zM7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3"/></symbol>
  <symbol id="i-user" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></symbol>
  <symbol id="i-logout" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></symbol>
  <symbol id="i-copy" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></symbol>
  <symbol id="i-share" viewBox="0 0 24 24"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></symbol>
  <symbol id="i-plus" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></symbol>
  <symbol id="i-play" viewBox="0 0 24 24"><polygon points="6 3 20 12 6 21 6 3"/></symbol>
  <symbol id="i-send" viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></symbol>
  <symbol id="i-close" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></symbol>
  <symbol id="i-zap" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></symbol>
</svg>

<div class="app">
  <header class="top-nav">
    <div class="brand-badge"><svg class="ic"><use href="#i-logo"/></svg></div>
    <div style="margin-inline-start: 8px;">
      <h1>شكون أنا؟</h1>
      <p style="font-size: 11px; color: var(--text-muted);">التحدي والمرح الجماعي</p>
    </div>
    <div class="grow"></div>
    <div class="nav-actions">
      <button class="icon-btn" id="langBtn"><span style="font-size:11px; font-weight:800; color:var(--primary-light);" id="langTxt">AR</span></button>
      <button class="icon-btn" id="leaderBtn"><svg class="ic"><use href="#i-trophy"/></svg></button>
      <button class="icon-btn" id="profileBtn"><svg class="ic"><use href="#i-user"/></svg></button>
      <button class="icon-btn hidden" id="leaveBtn"><svg class="ic"><use href="#i-logout"/></svg></button>
    </div>
  </header>

  <div class="status-pill offline" id="connPill" style="align-self: center; margin-bottom: 10px;">
    <span class="status-dot"></span><span id="connTxt">جاري الاتصال...</span>
  </div>

  <div id="toast" class="toast-msg"></div>

  <!-- شاشة التحميل -->
  <section id="bootView" style="text-align: center; padding: 70px 0;">
    <div class="spinner"></div><p style="color: var(--text-muted); font-weight: 700;">جاري فتح اللعبة والاتصال...</p>
  </section>

  <!-- الواجهة الرئيسية -->
  <section id="homeView" class="hidden">
    <div class="card" style="text-align: center; padding: 20px 16px;">
      <h2 style="font-size: 19px; font-weight: 900; margin-bottom: 6px;">تحدي التخمين والمندس</h2>
      <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">العب مع أصدقائك أو ابحث عن مباراة سريعة أونلاين!</p>
      
      <div class="row" style="margin-bottom: 10px;">
        <button class="btn" id="quickBtn" style="background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);">
          <svg class="ic"><use href="#i-zap"/></svg><span>لعب سريع عشوائي</span>
        </button>
      </div>

      <div class="row">
        <button class="btn" id="createBtn">
          <svg class="ic"><use href="#i-plus"/></svg><span>إنشاء غرفة خاصة</span>
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-title"><svg class="ic"><use href="#i-target"/></svg><span>الانضمام برمز الغرفة</span></div>
      <div class="row">
        <input id="joinCodeIn" class="field code-field" maxlength="5" placeholder="ABCDE">
        <button class="btn btn-sm" id="joinBtn"><span>انضمام</span></button>
      </div>
    </div>
  </section>

  <!-- غرفة الانتظار (Lobby) -->
  <section id="lobbyView" class="hidden">
    <div class="card" style="text-align: center;">
      <div style="font-size: 11.5px; color: var(--text-muted); font-weight: 700;">رمز الغرفة الرسمي</div>
      <div class="room-code" id="displayCode">-----</div>
      <div class="row" style="max-width: 260px; margin: 0 auto;">
        <button class="btn btn-secondary btn-sm" id="copyBtn"><svg class="ic"><use href="#i-copy"/></svg><span>نسخ</span></button>
        <button class="btn btn-secondary btn-sm" id="shareBtn"><svg class="ic"><use href="#i-share"/></svg><span>دعوة</span></button>
      </div>
    </div>

    <div class="card">
      <div class="card-title"><span>اللاعبون</span><span class="grow"></span><span id="playerCount">0 / 12</span></div>
      <div class="players-grid" id="playersList"></div>
    </div>

    <div class="card">
      <div class="card-title"><span>إعدادات اللعبة والنمط</span></div>
      <div style="margin-bottom: 10px;">
        <label style="font-size: 11.5px; color: var(--text-muted); font-weight: 700;">نمط اللعبة</label>
        <select id="selMode" class="field">
          <option value="classic">كلاسيكي (مخمن وبقية اللاعبين تلميحات)</option>
          <option value="undercover">المندس / الجاسوس (الكل يعرف الكلمة ما عدا الجاسوس)</option>
          <option value="taboo">الكلمات الممنوعة (تلميح دون ذكر 3 كلمات محظورة)</option>
        </select>
      </div>
      <div style="margin-bottom: 10px;">
        <label style="font-size: 11.5px; color: var(--text-muted); font-weight: 700;">الفئة</label>
        <select id="selCat" class="field"></select>
      </div>
      <div class="row">
        <div><label style="font-size: 11.5px; color: var(--text-muted); font-weight: 700;">الجولات</label><select id="selRounds" class="field"></select></div>
        <div><label style="font-size: 11.5px; color: var(--text-muted); font-weight: 700;">الوقت</label><select id="selTimer" class="field"></select></div>
      </div>
    </div>

    <p id="lobbyHint" style="font-size: 12px; text-align: center; margin-bottom: 12px; color: var(--text-muted); font-weight: 700;"></p>
    <button class="btn" id="startBtn"><svg class="ic"><use href="#i-play"/></svg><span>بدء المباراة</span></button>
  </section>

  <!-- شاشة اللعب النشطة -->
  <section id="gameView" class="hidden">
    <div class="card" style="text-align: center;">
      <div style="font-size: 12px; font-weight: 800; color: var(--primary-light); margin-bottom: 6px;" id="gameModeBanner">نمط كلاسيكي</div>
      <div style="font-size: 30px; font-weight: 900; line-height: 1;" id="timerSecs">60</div>
      <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 10px;">ثانية متبقية</div>

      <div style="font-weight: 700; color: var(--text-muted);" id="roleText">...</div>
      <div style="font-size: 26px; font-weight: 900; color: var(--gold); margin: 6px 0;" id="targetWord">...</div>
      
      <!-- الكلمات الممنوعة إن وجدت -->
      <div id="tabooBox" class="hidden" style="margin-top: 6px;">
        <div style="font-size: 11px; color: var(--danger); font-weight: 800; margin-bottom: 4px;">ممنوع استخدام هذه الكلمات في التلميح:</div>
        <div id="tabooWordsList"></div>
      </div>

      <div id="resultBanner" class="hidden" style="font-weight: 800; margin-top: 8px;"></div>
    </div>

    <div class="card hidden" id="clueCard">
      <div class="card-title"><svg class="ic"><use href="#i-bulb"/></svg><span>اكتب تلميحاً ذكياً</span></div>
      <div class="row">
        <input id="clueInput" class="field" maxlength="80" placeholder="اكتب التلميح هنا...">
        <button class="btn btn-sm" id="sendClueBtn"><svg class="ic"><use href="#i-send"/></svg></button>
      </div>
    </div>

    <div class="card hidden" id="guessCard">
      <div class="card-title"><svg class="ic"><use href="#i-target"/></svg><span>اكتب تخمينك للكلمة</span></div>
      <div class="row">
        <input id="guessInput" class="field" maxlength="40" placeholder="ما هي الكلمة المطلوبة؟">
        <button class="btn btn-sm" id="sendGuessBtn"><span>تخمين</span></button>
      </div>
    </div>

    <div class="row" style="margin-bottom: 10px;">
      <div class="card" style="margin: 0;"><div class="card-title">التلميحات</div><div id="cluesFeed" style="max-height: 140px; overflow-y: auto;"></div></div>
      <div class="card" style="margin: 0;"><div class="card-title">المحاولات</div><div id="guessesFeed" style="max-height: 140px; overflow-y: auto;"></div></div>
    </div>

    <!-- التفاعلات الحية العائمة -->
    <div class="reactions-bar">
      <button class="react-btn" onclick="sendReaction('👏')">👏</button>
      <button class="react-btn" onclick="sendReaction('🔥')">🔥</button>
      <button class="react-btn" onclick="sendReaction('😂')">😂</button>
      <button class="react-btn" onclick="sendReaction('🤔')">🤔</button>
      <button class="react-btn" onclick="sendReaction('😱')">😱</button>
    </div>
  </section>

  <!-- شاشة نهاية اللعبة -->
  <section id="endView" class="hidden">
    <div class="card" style="text-align: center; padding: 24px 16px;">
      <svg class="ic" style="width: 44px; height: 44px; color: var(--gold); margin-bottom: 8px;"><use href="#i-trophy"/></svg>
      <h2 style="font-size: 22px; font-weight: 900;" id="winnerTitle">...</h2>
      <p style="color: var(--text-muted); margin-top: 4px;" id="winnerSub">...</p>
    </div>
    <div class="card"><div class="card-title">الترتيب النهائي</div><div id="finalScores"></div></div>
    <div class="row">
      <button class="btn" id="restartBtn"><svg class="ic"><use href="#i-play"/></svg><span>جولة جديدة</span></button>
      <button class="btn btn-secondary" id="exitHomeBtn">الرئيسية</button>
    </div>
  </section>

  <!-- نافذة ليدربورد المتصدرين -->
  <div class="modal-overlay hidden" id="leaderModal">
    <div class="modal-box">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px;">
        <h3 style="display:flex; align-items:center; gap:8px;"><svg class="ic" style="color:var(--gold);"><use href="#i-trophy"/></svg><span>لوحة الصدارة</span></h3>
        <button class="icon-btn" id="closeLeaderBtn"><svg class="ic"><use href="#i-close"/></svg></button>
      </div>
      <div id="globalLeaderList"></div>
    </div>
  </div>

  <!-- نافذة البروفايل والرتب -->
  <div class="modal-overlay hidden" id="profileModal">
    <div class="modal-box">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px;">
        <h3 style="display:flex; align-items:center; gap:8px;"><svg class="ic"><use href="#i-user"/></svg><span>الملف الشخصي والرتبة</span></h3>
        <button class="icon-btn" id="closeProfileBtn"><svg class="ic"><use href="#i-close"/></svg></button>
      </div>
      <div style="text-align: center; padding: 6px 0 12px;">
        <div class="avatar-badge" id="profAvatar" style="width: 56px; height: 56px; font-size: 22px; margin: 0 auto 8px;">ل</div>
        <h4 style="font-size: 16px; font-weight: 800;" id="profName">لاعب</h4>
        <div class="badge-pill" id="profTitle" style="margin-top: 4px;">مبتدئ</div>
      </div>
      <div class="stat-grid">
        <div class="stat-card"><div class="stat-val" id="profScore">0</div><div class="stat-lbl">مجموع النقاط</div></div>
        <div class="stat-card"><div class="stat-val" id="profWins">0</div><div class="stat-lbl">مرات الفوز</div></div>
        <div class="stat-card"><div class="stat-val" id="profGames">0</div><div class="stat-lbl">مباريات لعبتها</div></div>
        <div class="stat-card"><div class="stat-val" id="profWinRate">0%</div><div class="stat-lbl">نسبة الفوز</div></div>
      </div>
    </div>
  </div>
</div>

<script>
const tg = window.Telegram?.WebApp;
try { tg?.ready(); tg?.expand(); } catch (_) {}

const $ = id => document.getElementById(id);
const VIEWS = ['homeView', 'lobbyView', 'gameView', 'endView'];
let ws = null, me = null, state = null, timerInterval = null;

// قراءة رمز الغرفة تلقائياً (من الرابط أو من معلمات المجموعات)
let currentRoomCode = new URLSearchParams(location.search).get('room')?.toUpperCase() || tg?.initDataUnsafe?.start_param?.toUpperCase() || null;

const CATEGORIES = {
  celebs: 'مشاهير وثقافة',
  football: 'كرة قدم وأندية',
  anime: 'شخصيات أنمي',
  food: 'أكلات ومأكولات',
  general: 'معلومات عامة'
};

const populateSelect = (el, arr) => {
  el.replaceChildren();
  for (const [val, label] of arr) el.add(new Option(label, val));
};
populateSelect($('selCat'), Object.entries(CATEGORIES));
populateSelect($('selRounds'), [3, 5, 8, 10].map(n => [n, `${n} جولات`]));
populateSelect($('selTimer'), [30, 45, 60, 90].map(n => [n, `${n} ثانية`]));

function switchView(viewId) {
  $('bootView').classList.add('hidden');
  VIEWS.forEach(v => $(v).classList.toggle('hidden', v !== viewId));
  $('leaveBtn').classList.toggle('hidden', viewId === 'homeView');
}

function toast(msg) {
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2400);
}

function sendMsg(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
}

function getTitleByScore(pts) {
  if (pts > 500) return 'أسطورة شكون أنا 🏆';
  if (pts > 200) return 'ثعلب التخمين 🦊';
  if (pts > 50) return 'محقق ذكي 🔍';
  return 'مبتدئ 🌱';
}

function updateProfileUI(u) {
  if (!u) return;
  $('profName').textContent = u.name;
  $('profAvatar').textContent = (u.name || 'ل')[0];
  $('profAvatar').style.background = `hsl(${Math.abs(u.id * 53)%360},65%,45%)`;
  const s = u.stats || {};
  $('profScore').textContent = s.score || 0;
  $('profWins').textContent = s.wins || 0;
  $('profGames').textContent = s.games || 0;
  const rate = s.games ? Math.round((s.wins / s.games) * 100) : 0;
  $('profWinRate').textContent = `${rate}%`;
  $('profTitle').textContent = getTitleByScore(s.score || 0);
}

function connectServer() {
  const protocol = location.protocol === 'https:' ? 'wss://' : 'ws://';
  const host = location.host || 'chkon-ana.onrender.com';
  ws = new WebSocket(`${protocol}${host}/ws`);

  ws.onopen = () => {
    $('connPill').classList.remove('offline');
    $('connTxt').textContent = 'متصل';
    sendMsg({
      type: 'auth',
      initData: tg?.initData || '',
      user: tg?.initDataUnsafe?.user || null
    });
  };

  ws.onmessage = ev => {
    try {
      const m = JSON.parse(ev.data);
      if (m.type === 'authed') {
        me = m.user;
        updateProfileUI(me);
        if (currentRoomCode) sendMsg({ type: 'join', code: currentRoomCode });
        else switchView('homeView');
      } else if (m.type === 'state') {
        state = m.state;
        currentRoomCode = state.code;
        render();
      } else if (m.type === 'reaction') {
        spawnReaction(m.emoji);
      } else if (m.type === 'leaderboard') {
        renderLeaderboard(m.data);
      } else if (m.type === 'error') {
        toast(m.message);
        if (!state) switchView('homeView');
      }
    } catch (_) {}
  };

  ws.onclose = () => {
    $('connPill').classList.add('offline');
    $('connTxt').textContent = 'جاري إعادة الاتصال...';
    setTimeout(connectServer, 2000);
  };
}

// حزام أمان ذكي ضد التعليق
setTimeout(() => {
  if (!me) {
    me = tg?.initDataUnsafe?.user || { id: Math.floor(100000 + Math.random()*900000), first_name: "لاعب" };
    me.name = me.first_name || me.name || "لاعب";
    updateProfileUI(me);
    switchView('homeView');
  }
}, 3000);

function sendReaction(emoji) {
  sendMsg({ type: 'reaction', emoji });
  spawnReaction(emoji);
}

function spawnReaction(emoji) {
  const el = document.createElement('div');
  el.className = 'flying-reaction';
  el.textContent = emoji;
  el.style.left = `${30 + Math.random() * 40}%`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 1800);
}

function launchConfetti() {
  const canvas = $('confettiCanvas');
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  const pieces = Array.from({length: 60}, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height - canvas.height,
    size: Math.random() * 8 + 4,
    color: ['#9333ea', '#3b82f6', '#eab308', '#10b981', '#ef4444'][Math.floor(Math.random()*5)],
    velY: Math.random() * 3 + 2,
    velX: Math.random() * 2 - 1
  }));
  let frames = 0;
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    pieces.forEach(p => {
      ctx.fillStyle = p.color;
      ctx.fillRect(p.x, p.y, p.size, p.size);
      p.y += p.velY;
      p.x += p.velX;
    });
    frames++;
    if (frames < 120) requestAnimationFrame(draw);
    else ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
  draw();
}

const getPlayerName = id => state?.players.find(p => p.id === id)?.name || 'لاعب';

function render() {
  if (!state || !me) return switchView('homeView');

  if (state.status === 'lobby') {
    switchView('lobbyView');
    const isHost = state.host === me.id;
    $('displayCode').textContent = state.code;
    $('playerCount').textContent = `${state.players.length} / 12`;
    $('selMode').value = state.settings.mode || 'classic';
    $('selCat').value = state.settings.category;
    $('selRounds').value = state.settings.rounds;
    $('selTimer').value = state.settings.timer;
    ['selMode', 'selCat', 'selRounds', 'selTimer'].forEach(id => { $(id).disabled = !isHost; });
    $('startBtn').disabled = !isHost || state.players.length < 2;

    const list = $('playersList');
    list.replaceChildren();
    state.players.forEach(p => {
      const d = document.createElement('div');
      d.className = 'player-item';
      d.innerHTML = `<div class="avatar-badge" style="background: hsl(${Math.abs(p.id * 53)%360},65%,45%)">${(p.name||'ل')[0]}</div>
                     <div class="player-name">${p.name}${p.id===me.id?' (أنت)':''} ${p.id===state.host?'👑':''}</div>`;
      list.appendChild(d);
    });
  } else if (state.status === 'playing') {
    switchView('gameView');
    const r = state.round;
    const mode = state.settings.mode || 'classic';
    const isGuesser = r.guesser === me.id;
    const isImpostor = r.impostor === me.id;

    if (mode === 'undercover') {
      $('gameModeBanner').textContent = '🕵️ نمط المندس / الجاسوس';
      $('roleText').textContent = isImpostor ? '🚨 أنت هو المندس! لا تدعهم يكتشفونك!' : '🔍 اكتب تلميحك واكتشف المندس بينكم';
      $('targetWord').textContent = isImpostor ? '❓ [أنت المندس]' : r.word;
    } else if (mode === 'taboo') {
      $('gameModeBanner').textContent = '🚫 نمط الكلمات الممنوعة (Taboo)';
      $('roleText').textContent = isGuesser ? '🎯 دورك للتخمين الآن' : `💡 المخمن: ${getPlayerName(r.guesser)}`;
      $('targetWord').textContent = r.word || 'ـ ـ ـ ـ ـ ـ';
    } else {
      $('gameModeBanner').textContent = '🎯 النمط الكلاسيكي';
      $('roleText').textContent = isGuesser ? '🎯 دورك للتخمين الآن' : `💡 المخمن: ${getPlayerName(r.guesser)}`;
      $('targetWord').textContent = r.word || 'ـ ـ ـ ـ ـ ـ';
    }

    if (mode === 'taboo' && !isGuesser && r.taboo && r.taboo.length) {
      $('tabooBox').classList.remove('hidden');
      $('tabooWordsList').innerHTML = r.taboo.map(w => `<span class="taboo-tag">${w}</span>`).join('');
    } else {
      $('tabooBox').classList.add('hidden');
    }

    $('clueCard').classList.toggle('hidden', (mode !== 'undercover' && isGuesser) || !r.active);
    $('guessCard').classList.toggle('hidden', (mode !== 'undercover' && !isGuesser) || !r.active);

    const banner = $('resultBanner');
    if (!r.active) {
      banner.classList.remove('hidden');
      banner.textContent = r.solved ? '🎉 تم التخمين بنجاح!' : '⏰ انتهى الوقت!';
      banner.style.color = r.solved ? 'var(--success)' : 'var(--danger)';
      if (r.solved) launchConfetti();
    } else {
      banner.classList.add('hidden');
    }

    const cFeed = $('cluesFeed'); cFeed.replaceChildren();
    r.clues.forEach(c => {
      const item = document.createElement('div');
      item.style.padding = '4px 0';
      item.innerHTML = `<b>${getPlayerName(c.by)}:</b> ${c.text}`;
      cFeed.appendChild(item);
    });

    const gFeed = $('guessesFeed'); gFeed.replaceChildren();
    r.guesses.forEach(g => {
      const item = document.createElement('div');
      item.style.padding = '4px 0';
      item.textContent = `${g.text} ${g.ok ? '✅' : ''}`;
      gFeed.appendChild(item);
    });

    clearInterval(timerInterval);
    const end = Date.now() + r.left;
    const updateTimer = () => {
      const rem = r.active ? Math.max(0, end - Date.now()) : 0;
      $('timerSecs').textContent = Math.ceil(rem / 1000);
    };
    updateTimer();
    if (r.active) timerInterval = setInterval(updateTimer, 250);
  } else if (state.status === 'ended') {
    switchView('endView');
    clearInterval(timerInterval);
    launchConfetti();
    const sorted = [...state.players].sort((a,b)=>b.score-a.score);
    $('winnerTitle').textContent = `الفائز: ${sorted[0]?.name || 'لا أحد'}`;
    $('winnerSub').textContent = `الرصيد: ${sorted[0]?.score || 0} نقطة`;

    const fBox = $('finalScores'); fBox.replaceChildren();
    sorted.forEach((p, idx) => {
      const row = document.createElement('div');
      row.style.display = 'flex';
      row.style.padding = '8px 0';
      row.style.borderBottom = '1px solid var(--border)';
      row.innerHTML = `<span style="width:24px; font-weight:800;">${idx+1}</span>
                       <span style="flex:1; font-weight:700;">${p.name}</span>
                       <b style="color:var(--gold);">${p.score} ن</b>`;
      fBox.appendChild(row);
    });
    $('restartBtn').classList.toggle('hidden', state.host !== me.id);
  }
}

function renderLeaderboard(list) {
  const box = $('globalLeaderList');
  box.replaceChildren();
  list.forEach(p => {
    const row = document.createElement('div');
    row.style.display = 'flex';
    row.style.alignItems = 'center';
    row.style.padding = '8px 0';
    row.style.borderBottom = '1px solid var(--border)';
    row.innerHTML = `<span style="width:24px; font-weight:800;">${p.rank}</span>
                     <span style="flex:1; font-weight:700;">${p.name}</span>
                     <span style="font-size:12px; color:var(--text-muted); margin-inline-end:8px;">🏆 ${p.wins}</span>
                     <b style="color:var(--gold);">${p.score} ن</b>`;
    box.appendChild(row);
  });
}

function leave() {
  sendMsg({ type: 'leave' });
  state = null; currentRoomCode = null; clearInterval(timerInterval);
  switchView('homeView');
}

$('createBtn').onclick = () => sendMsg({ type: 'create' });
$('quickBtn').onclick = () => sendMsg({ type: 'quick_match' });
$('joinBtn').onclick = () => {
  const code = $('joinCodeIn').value.trim().toUpperCase();
  if (code.length === 5) sendMsg({ type: 'join', code });
};

$('copyBtn').onclick = () => {
  if (state?.code) { navigator.clipboard?.writeText(state.code); toast('تم نسخ رمز الغرفة'); }
};
$('shareBtn').onclick = () => {
  if (!state?.code) return;
  const shareText = `العب معي «شكون أنا؟» في تيليجرام!\nرمز الغرفة: ${state.code}`;
  const url = `https://t.me/share/url?url=${encodeURIComponent('https://t.me/chkonanabot?start=' + state.code)}&text=${encodeURIComponent(shareText)}`;
  if (tg?.openTelegramLink) tg.openTelegramLink(url);
  else window.open(url, '_blank');
};

$('startBtn').onclick = () => sendMsg({ type: 'start' });
$('restartBtn').onclick = () => sendMsg({ type: 'restart' });
$('leaveBtn').onclick = leave;
$('exitHomeBtn').onclick = leave;

$('leaderBtn').onclick = () => {
  sendMsg({ type: 'get_leaderboard' });
  $('leaderModal').classList.remove('hidden');
};
$('closeLeaderBtn').onclick = () => $('leaderModal').classList.add('hidden');

$('profileBtn').onclick = () => {
  if (me) updateProfileUI(me);
  $('profileModal').classList.remove('hidden');
};
$('closeProfileBtn').onclick = () => $('profileModal').classList.add('hidden');

['selMode', 'selCat', 'selRounds', 'selTimer'].forEach(id => {
  $(id).onchange = () => sendMsg({
    type: 'settings',
    mode: $('selMode').value,
    category: $('selCat').value,
    rounds: Number($('selRounds').value),
    timer: Number($('selTimer').value)
  });
});

$('sendClueBtn').onclick = () => {
  const val = $('clueInput').value.trim();
  if (val) { sendMsg({ type: 'clue', text: val }); $('clueInput').value = ''; }
};
$('sendGuessBtn').onclick = () => {
  const val = $('guessInput').value.trim();
  if (val) { sendMsg({ type: 'guess', text: val }); $('guessInput').value = ''; }
};

connectServer();
</script>
</body>
</html>"""

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).replace("\u0640", "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.translate(str.maketrans("أإآىةؤئ", "ااايهوي")).lower()
    return re.sub(r"[\W_]+", "", s)

def strip_al(s: str) -> str:
    if s.startswith("ال") and len(s) > 3:
        return s[2:]
    return s

def is_guess_match(guess: str, target: str) -> bool:
    g, t = norm(guess), norm(target)
    if not g or not t:
        return False
    return g == t or strip_al(g) == strip_al(t)

def clue_has_forbidden_word(clue: str, target: str, taboo_list=None) -> bool:
    n_clue = norm(clue)
    n_target = norm(target)
    if not n_clue or not n_target:
        return False
    if n_target in n_clue or strip_al(n_target) in n_clue:
        return True
    parts = [norm(p) for p in target.split() if len(norm(p)) >= 3]
    for p in parts:
        sp = strip_al(p)
        if len(sp) >= 3 and sp in n_clue:
            return True
    if taboo_list:
        for tb in taboo_list:
            n_tb = norm(tb)
            if n_tb and n_tb in n_clue:
                return True
    return False

def verify_init_data(raw: str):
    if not raw:
        return None
    try:
        vals = {}
        for part in raw.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                vals[k] = unquote(v)
        received_hash = vals.pop("hash", "")
        vals.pop("signature", None)
        if not received_hash:
            return None
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(vals.items()))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.strip().encode(), hashlib.sha256).digest()
        expected_hash = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected_hash, received_hash) and "user" in vals:
            user = json.loads(vals["user"])
            return {
                "id": int(user["id"]),
                "name": str(user.get("first_name", "لاعب")).strip()[:20] or "لاعب",
            }
    except Exception:
        pass
    return None

async def send(ws, data):
    try:
        await ws.send_str(json.dumps(data, ensure_ascii=False))
    except Exception:
        pass

def err(msg):
    return {"type": "error", "message": msg}

ROOMS = {}

class Room:
    def __init__(self, code, host):
        self.code = code
        self.host = host
        self.status = "lobby"
        self.settings = {"mode": "classic", "category": "general", "rounds": 5, "timer": 60}
        self.players = {}
        self.order = []
        self.conns = {}
        self.used_words = set()
        self.round = None
        self.no = 0
        self.token = 0
        self.touched = time.time()

    def state_for(self, uid):
        r = self.round
        rnd = None
        if r:
            mode = self.settings.get("mode", "classic")
            word_to_show = r["word"]
            if mode == "undercover":
                word_to_show = None if uid == r["impostor"] else r["word"]
            elif mode == "classic" or mode == "taboo":
                word_to_show = r["word"] if (not r["active"] or uid != r["guesser"]) else None

            rnd = {
                "no": r["no"],
                "total": self.settings["rounds"],
                "guesser": r["guesser"],
                "impostor": r.get("impostor"),
                "active": r["active"],
                "solved": r["solved"],
                "left": max(0, int((r["end"] - time.time()) * 1000)),
                "word": word_to_show,
                "taboo": r.get("taboo", []),
                "clues": r["clues"],
                "guesses": r["guesses"],
            }
        return {
            "code": self.code,
            "host": self.host,
            "status": self.status,
            "settings": self.settings,
            "players": [
                {
                    "id": p,
                    "name": self.players[p]["name"],
                    "score": self.players[p]["score"],
                    "online": p in self.conns,
                }
                for p in self.order
            ],
            "round": rnd,
        }

    async def broadcast(self):
        self.touched = time.time()
        for uid, ws in list(self.conns.items()):
            await send(ws, {"type": "state", "state": self.state_for(uid)})

    async def join(self, uid, name, ws):
        if uid not in self.players:
            self.order.append(uid)
            self.players[uid] = {"name": name, "score": 0}
        self.players[uid]["name"] = name
        self.conns[uid] = ws
        await self.broadcast()

    def pick_word_item(self):
        cat = self.settings["category"]
        pool = [item for item in WORDS_DATA.get(cat, WORDS_DATA["general"]) if item["word"] not in self.used_words]
        if not pool:
            self.used_words.clear()
            pool = WORDS_DATA.get(cat, WORDS_DATA["general"])
        chosen = random.choice(pool)
        self.used_words.add(chosen["word"])
        return chosen

    def start_round(self):
        if not self.order:
            self.status = "lobby"
            return
        self.no += 1
        self.token += 1
        secs = self.settings["timer"]

        online_candidates = [p for p in self.order if p in self.conns]
        if not online_candidates:
            self.status = "ended"
            return

        active_guesser = self.order[(self.no - 1) % len(self.order)]
        if active_guesser not in self.conns:
            active_guesser = online_candidates[0]

        impostor = random.choice(online_candidates) if self.settings.get("mode") == "undercover" else None
        item = self.pick_word_item()

        self.round = {
            "no": self.no,
            "word": item["word"],
            "taboo": item.get("taboo", []),
            "guesser": active_guesser,
            "impostor": impostor,
            "active": True,
            "solved": False,
            "end": time.time() + secs,
            "clues": [],
            "guesses": [],
            "gn": set(),
        }
        asyncio.create_task(self._timeout(self.token, secs))

    async def _timeout(self, token, secs):
        await asyncio.sleep(secs)
        if token == self.token and self.round and self.round["active"]:
            await self.end_round(None)

    async def end_round(self, winner):
        r = self.round
        if not r:
            return
        r["active"] = False
        r["solved"] = winner is not None

        if winner is not None and winner in self.players:
            self.players[winner]["score"] += 10
            for uid in {c["by"] for c in r["clues"]}:
                if uid in self.players:
                    self.players[uid]["score"] += 2

        if self.no >= self.settings["rounds"]:
            self.status = "ended"
            sorted_p = sorted(self.players.items(), key=lambda x: x[1]["score"], reverse=True)
            top_score = sorted_p[0][1]["score"] if sorted_p else 0
            for uid, p in self.players.items():
                is_win = (p["score"] == top_score and top_score > 0)
                update_user_stats(uid, p["name"], add_score=p["score"], won=is_win)

        await self.broadcast()
        if self.status == "playing":
            asyncio.create_task(self._next(self.no))

    async def _next(self, no):
        await asyncio.sleep(4.5)
        if self.status == "playing" and self.no == no:
            self.start_round()
            await self.broadcast()

    async def handle(self, uid, t, data):
        r = self.round
        if t == "settings":
            if uid != self.host or self.status != "lobby":
                return "لا يمكنك تغيير الإعدادات الآن"
            self.settings["mode"] = data.get("mode", "classic")
            self.settings["category"] = data.get("category", "general")
            self.settings["rounds"] = data.get("rounds", 5)
            self.settings["timer"] = data.get("timer", 60)
            await self.broadcast()
            return None

        if t == "start":
            if uid != self.host or self.status != "lobby":
                return "فقط المضيف يمكنه البدء"
            if len([p for p in self.order if p in self.conns]) < 2:
                return "يلزم لاعبين على الأقل للبدء"
            self.status = "playing"
            self.no = 0
            self.used_words.clear()
            for p in self.players.values():
                p["score"] = 0
            self.start_round()
            await self.broadcast()
            return None

        if t == "restart":
            if uid != self.host or self.status != "ended":
                return "فقط المضيف يمكنه إعادة اللعب"
            self.status = "lobby"
            self.round = None
            self.no = 0
            self.used_words.clear()
            for p in self.players.values():
                p["score"] = 0
            await self.broadcast()
            return None

        if t == "clue":
            if self.status != "playing" or not r or not r["active"]:
                return "ليس متاحاً لك الآن"
            mode = self.settings.get("mode", "classic")
            if mode != "undercover" and uid == r["guesser"]:
                return "المخمن لا يقدم تلميحاً"
            text = str(data.get("text", "")).strip()[:80]
            if not text:
                return "يرجى كتابة نص"
            taboo = r.get("taboo", []) if mode == "taboo" else []
            if clue_has_forbidden_word(text, r["word"], taboo):
                return "ممنوع ذكر الكلمة أو إحدى الكلمات المحظورة في التلميح!"
            r["clues"].append({"by": uid, "text": text})
            await self.broadcast()
            return None

        if t == "guess":
            if self.status != "playing" or not r or not r["active"]:
                return "غير متاح الآن"
            mode = self.settings.get("mode", "classic")
            if mode != "undercover" and uid != r["guesser"]:
                return "ليس دورك في التخمين"
            text = str(data.get("text", "")).strip()[:40]
            n = norm(text)
            if not n:
                return "إجابة غير صالحة"
            if n in r["gn"]:
                return "تمت تجربتها مسبقاً"
            r["gn"].add(n)
            ok = is_guess_match(text, r["word"])
            r["guesses"].append({"text": text, "ok": ok})
            if ok:
                await self.end_round(uid)
            else:
                await self.broadcast()
            return None
        return None

async def detach(room, uid, ws):
    if not room or room.conns.get(uid) is not ws:
        return
    del room.conns[uid]
    if room.status == "lobby":
        if uid in room.players:
            del room.players[uid]
        if uid in room.order:
            room.order.remove(uid)
    if uid == room.host:
        candidates = [p for p in room.order if p in room.conns]
        if candidates:
            room.host = candidates[0]
    if room.status == "playing" and room.round and room.round["active"]:
        if room.round["guesser"] == uid:
            await room.end_round(None)
            return
    await room.broadcast()

def new_code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    while True:
        code = "".join(random.choices(alphabet, k=5))
        if code not in ROOMS:
            return code

async def ws_handler(request):
    ws = web.WebSocketResponse(heartbeat=25)
    await ws.prepare(request)
    uid = name = room = None
    last_act = 0.0

    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue
            try:
                data = json.loads(msg.data)
            except ValueError:
                continue

            t = data.get("type")
            if t in ("clue", "guess"):
                now = time.time()
                if now - last_act < 0.35:
                    await send(ws, err("تمهل قليلاً"))
                    continue
                last_act = now

            if t == "reaction":
                emoji = data.get("emoji", "🔥")
                if room:
                    for p_ws in room.conns.values():
                        if p_ws is not ws:
                            await send(p_ws, {"type": "reaction", "emoji": emoji})
                continue

            if t == "get_leaderboard":
                await send(ws, {"type": "leaderboard", "data": get_leaderboard_data()})
                continue

            if t == "auth":
                raw_init = str(data.get("initData", ""))
                user = verify_init_data(raw_init)
                if not user:
                    tg_user = data.get("user")
                    if tg_user and isinstance(tg_user, dict) and tg_user.get("id"):
                        user = {
                            "id": int(tg_user["id"]),
                            "name": str(tg_user.get("first_name", "لاعب")).strip()[:20] or "لاعب"
                        }
                    elif "user=" in raw_init:
                        try:
                            for part in raw_init.split("&"):
                                if part.startswith("user="):
                                    u = json.loads(unquote(part[5:]))
                                    user = {
                                        "id": int(u["id"]),
                                        "name": str(u.get("first_name", "لاعب")).strip()[:20] or "لاعب"
                                    }
                                    break
                        except Exception:
                            pass
                if not user:
                    rnd_id = random.randint(100000, 999999)
                    user = {"id": rnd_id, "name": f"لاعب {str(rnd_id)[-3:]}"}

                uid, name = user["id"], user["name"]
                s = STATS.get(str(uid), {"score": 0, "wins": 0, "games": 0})
                user["stats"] = s
                await send(ws, {"type": "authed", "user": user})

            elif uid is None:
                continue

            elif t == "quick_match":
                target = None
                for r in ROOMS.values():
                    if r.status == "lobby" and len(r.players) < MAX_PLAYERS:
                        target = r
                        break
                if not target:
                    code = new_code()
                    target = ROOMS[code] = Room(code, uid)
                await detach(room, uid, ws)
                room = target
                await room.join(uid, name, ws)

            elif t in ("create", "join"):
                if t == "create":
                    code = new_code()
                    target = ROOMS[code] = Room(code, uid)
                else:
                    target = ROOMS.get(str(data.get("code", "")).upper().strip())
                    if target is None:
                        await send(ws, err("رمز الغرفة غير صحيح"))
                        continue
                    if uid not in target.players and (target.status != "lobby" or len(target.players) >= MAX_PLAYERS):
                        await send(ws, err("الغرفة ممتلئة أو جارية"))
                        continue
                await detach(room, uid, ws)
                room = target
                await room.join(uid, name, ws)

            elif t == "leave":
                await detach(room, uid, ws)
                room = None

            elif room is not None:
                try:
                    error = await room.handle(uid, t, data)
                except Exception:
                    error = "خطأ في معالجة الطلب"
                if error:
                    await send(ws, err(error))
    finally:
        await detach(room, uid, ws)
    return ws

async def cleanup():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        for code, room in list(ROOMS.items()):
            if not room.conns and (now - room.touched > 1200):
                del ROOMS[code]

async def index(_):
    return web.Response(text=HTML_PAGE, content_type="text/html", charset="utf-8")

# --- نظام البوت التفاعلي في المجموعات والمحادثات الخاصة ---
async def send_tg_msg(session, chat_id, text, reply_markup=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        await session.post(url, json=payload)
    except Exception:
        pass

async def handle_tg_message(session, msg):
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    chat_type = chat.get("type", "private")
    user = msg.get("from", {})
    user_id = user.get("id")
    username = (user.get("username") or "").lower()
    text = (msg.get("text") or "").strip()
    if not chat_id:
        return

    # حفظ المستخدمين للإذاعة
    if user_id:
        USERS.add(user_id)
        save_db(USERS_FILE, {str(u): True for u in USERS})

    is_owner = (user_id == OWNER_ID) or (username == OWNER_USERNAME.lower())

    # ترحيب عند إضافة البوت إلى مجموعة جديدة
    if "new_chat_members" in msg:
        for m in msg["new_chat_members"]:
            if m.get("is_bot") and m.get("username", "").lower() == "chkonanabot":
                await send_tg_msg(
                    session,
                    chat_id,
                    "👋 مرحباً بكم في لعبة «شكون أنا؟» في مجموعتكم! 🎮\n\n"
                    "اكتبوا الأمر /play لبدء مباراة وتحدي بين أعضاء المجموعة فوراً!"
                )
                return

    # تنظيف الأمر من اسم البوت (مثلاً /play@chkonanabot -> /play)
    clean_cmd = text.split("@")[0].lower() if text.startswith("/") else ""

    # تشغيل اللعبة في المجموعات (Groups & Supergroups)
    if chat_type in ("group", "supergroup"):
        if clean_cmd in ("/start", "/play", "/game"):
            # البحث عن غرفة سابقة للمجموعة أو إنشاء واحدة جديدة
            code = GROUP_ROOMS.get(chat_id)
            if not code or code not in ROOMS or ROOMS[code].status == "ended":
                code = new_code()
                ROOMS[code] = Room(code, user_id)
                GROUP_ROOMS[chat_id] = code

            url = f"{APP_URL}?room={code}"
            group_kb = {
                "inline_keyboard": [
                    [{"text": "🎮 دخول غرفة المجموعة • Join Game", "web_app": {"url": url}}]
                ]
            }
            await send_tg_msg(
                session,
                chat_id,
                f"🎯 تم فتح غرفة اللعب الخاصة بمجموعتكم!\n"
                f"🔑 رمز الغرفة: <code>{code}</code>\n\n"
                f"اضغطوا جميعاً على الزر بالأسفل للدخول معاً لنفس الغرفة وبدء المباراة 👇",
                reply_markup=group_kb
            )
            return

    # تشغيل اللعبة في الخاص (Private Chat)
    if chat_type == "private":
        if clean_cmd == "/start":
            private_kb = {
                "inline_keyboard": [
                    [{"text": "🎮 العب الآن • Play", "web_app": {"url": APP_URL}}],
                    [{"text": "➕ أضف البوت لمجموعتك", "url": "https://t.me/chkonanabot?startgroup=true"}]
                ]
            }
            await send_tg_msg(
                session,
                chat_id,
                "مرحباً بك في منصة «شكون أنا؟» 🎮\n\n"
                "• اضغط على «العب الآن» لفتح اللعبة في الخاص.\n"
                "• أو أضف البوت إلى مجموعتك والعبوا معاً في غرفة موحدة!",
                reply_markup=private_kb
            )
        elif clean_cmd == "/stats" and is_owner:
            await send_tg_msg(
                session,
                chat_id,
                f"👑 إحصائيات المالك ({OWNER_USERNAME}):\n"
                f"- إجمالي اللاعبين المسجلين: {len(STATS)}\n"
                f"- الغرف النشطة الآن: {len(ROOMS)}\n"
                f"- مستخدمو البوت: {len(USERS)}"
            )
        elif clean_cmd == "/broadcast" and is_owner:
            args = text.split(maxsplit=1)
            if len(args) > 1:
                bc_text = args[1]
                sent = 0
                for uid in list(USERS):
                    try:
                        await send_tg_msg(session, uid, bc_text)
                        sent += 1
                        await asyncio.sleep(0.04)
                    except Exception:
                        pass
                await send_tg_msg(session, chat_id, f"تم إرسال الإذاعة إلى {sent} مستخدماً.")

async def bot_polling():
    offset = 0
    async with aiohttp.ClientSession() as session:
        try:
            await session.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true")
        except Exception:
            pass

        while True:
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=20"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for update in data.get("result", []):
                            offset = update["update_id"] + 1
                            if "message" in update:
                                await handle_tg_message(session, update["message"])
            except Exception:
                await asyncio.sleep(3)
            await asyncio.sleep(0.4)

async def main():
    app = web.Application()
    app.add_routes([web.get("/", index), web.get("/ws", ws_handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()

    asyncio.create_task(cleanup())
    asyncio.create_task(bot_polling())

    print(f"Server is running on port {PORT} for Owner: @{OWNER_USERNAME} ({OWNER_ID})...")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
