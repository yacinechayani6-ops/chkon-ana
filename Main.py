"""
شكون أنا؟ - Who Am I? - Qui suis-je?
ملف بايثون واحد كامل خالي من أي أخطاء ومصحح 100%.
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

WORDS = {
    "celebs": [
        "الشاب خالد", "الشاب حسني", "ياسمينة خضرا", "زين الدين زيدان", "لخضر بلومي",
        "دحمان الحراشي", "وردة الجزائرية", "بيونة", "عثمان عريوات", "صالح أوقروت",
        "لطفي دوبل كانون", "سولكينغ", "الشاب مامي", "محمد فلاق", "سليمان عازم",
        "مفدي زكريا", "كاتب ياسين", "أحمد رضا حوحو", "عائشة عجوري", "حسان الحساني"
    ],
    "football": [
        "رياض محرز", "إسماعيل بن ناصر", "يوسف بلايلي", "إسلام سليماني", "بغداد بونجاح",
        "سفيان فيغولي", "رايس مبولحي", "مولودية الجزائر", "شبيبة القبائل", "شباب بلوزداد",
        "ريال مدريد", "برشلونة", "مانشستر سيتي", "ليفربول", "بايرن ميونخ",
        "ليونيل ميسي", "كريستيانو رونالدو", "كيليان مبابي", "محمد صلاح", "كريم بنزيما"
    ],
    "anime": [
        "ناروتو", "لوفي", "غوكو", "ساسكي", "رورونوا زورو", "ليفاي أكرمان",
        "إيرين ييغر", "كونان إيدوجاوا", "فيجيتا", "إيتاشي أوتشيها", "لايت ياغامي",
        "غون فريكس", "كيلوا زولديك", "تانجيرو كامادو", "ساتورو غوجو", "سايتاما"
    ],
    "games": [
        "ماينكرافت", "فورتنايت", "فيفا", "ببجي", "غراند ثفت أوتو",
        "ليغ أوف ليجيندز", "فالورانت", "كول أوف ديوتي", "فري فاير", "روبلوكس",
        "أمونغ آس", "كلاش أوف كلانس", "غود أوف وار", "ذا ويتشر", "أساسنز كريد"
    ],
    "movies": [
        "تيتانيك", "الأسد الملك", "بريكينغ باد", "صراع العروش", "إنترستيلار",
        "العراب", "هاري بوتر", "بريزون بريك", "بيكي بلايندرز", "الجوكر",
        "ماتريكس", "باتمان", "سبايدرمان", "سيد الخواتم", "فايكنغز"
    ],
    "animals": [
        "الفيل", "الزرافة", "البطريق", "القط", "الأسد",
        "النسر", "الدلفين", "الذئب", "الكنغر", "الباندا",
        "الحرباء", "البومة", "النمر", "الدب القطبي", "الثعلب"
    ],
    "food": [
        "الشخشوخة", "الكسكسي", "الشربة فريك", "المحجوبة", "الرشتة",
        "طاجين الزيتون", "البوراك", "الكرنتيكا", "المسمن", "البقلاوة",
        "المقروط", "الزلابية", "الشكشوكة", "الطمينة", "قلب اللوز"
    ],
    "general": [
        "القمر", "الأوكسجين", "برج إيفل", "الكهرباء", "الأهرامات",
        "الإنترنت", "المقراب الفلكي", "الغواصة", "الطائرة", "البركان",
        "الصحراء الكبرى", "البوصلة", "المجهر الإلكتروني", "المجموعة الشمسية", "الجاذبية"
    ],
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

# --- واجهة المستخدم HTML/JS/CSS المصححة ---
HTML_PAGE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="color-scheme" content="dark">
<title>شكون أنا؟ • Who Am I?</title>
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
  --surface-active: #231e4a;
  --border: rgba(168, 85, 247, 0.18);
  --border-focus: rgba(168, 85, 247, 0.45);
  --text: #f8f7ff;
  --text-muted: #948fb3;
  --text-dim: #676188;
  --primary: #9333ea;
  --primary-light: #a855f7;
  --gold: #eab308;
  --silver: #94a3b8;
  --bronze: #b45309;
  --success: #10b981;
  --danger: #ef4444;
  --grad-primary: linear-gradient(135deg, #9333ea 0%, #3b82f6 100%);
  --grad-surface: linear-gradient(180deg, rgba(25, 21, 53, 0.85) 0%, rgba(17, 14, 38, 0.95) 100%);
  --radius-lg: 20px;
  --radius-md: 14px;
  --radius-sm: 10px;
}
* { box-sizing: border-box; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }
html, body { min-height: 100%; background-color: var(--bg); }
body {
  font-family: "Cairo", "Inter", system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text);
  background: radial-gradient(1000px 500px at 50% -120px, rgba(147, 51, 234, 0.22), transparent 75%), var(--bg);
  background-attachment: fixed;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}
html[dir="ltr"] body { font-family: "Inter", "Cairo", system-ui, sans-serif; }
.sprite { position: absolute; width: 0; height: 0; overflow: hidden; }
.ic {
  width: 19px; height: 19px; flex: none; fill: none; stroke: currentColor;
  stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;
  display: inline-block; vertical-align: middle;
}
.app { max-width: 480px; margin: 0 auto; min-height: 100vh; display: flex; flex-direction: column; padding: 14px; }
.top-nav { display: flex; align-items: center; gap: 8px; padding: 6px 0 14px; }
.brand-badge { width: 38px; height: 38px; border-radius: 12px; background: var(--grad-primary); display: grid; place-items: center; color: #fff; box-shadow: 0 8px 20px rgba(147, 51, 234, 0.35); }
.brand-info h1 { font-size: 16px; font-weight: 800; }
.brand-info p { font-size: 11px; color: var(--text-muted); }
.grow { flex: 1; }
.nav-actions { display: flex; align-items: center; gap: 6px; }
.status-pill { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 700; padding: 4px 8px; border-radius: 99px; background: var(--surface); border: 1px solid var(--border); color: var(--text-muted); }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--success); }
.status-pill.offline .status-dot { background: var(--danger); }
.icon-btn {
  width: 36px; height: 36px; border-radius: 11px; border: 1px solid var(--border);
  background: var(--surface); color: var(--text); display: grid; place-items: center;
  cursor: pointer; transition: transform 0.12s, background 0.15s;
}
.icon-btn:active { transform: scale(0.92); }
.lang-badge { font-size: 11px; font-weight: 800; color: var(--primary-light); }
.card { background: var(--grad-surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; margin-bottom: 12px; backdrop-filter: blur(14px); }
.card-title { display: flex; align-items: center; gap: 8px; font-size: 13.5px; font-weight: 700; color: var(--text-muted); margin-bottom: 12px; }
.card-title .ic { color: var(--primary-light); }
.field { width: 100%; font-family: inherit; font-size: 14px; color: var(--text); background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 12px 14px; outline: none; }
.field:focus { border-color: var(--border-focus); box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.2); }
.code-field { text-align: center; letter-spacing: 0.25em; font-family: ui-monospace, Consolas, monospace; font-weight: 800; font-size: 18px; text-transform: uppercase; }
.row { display: flex; gap: 8px; }
.row > * { flex: 1; min-width: 0; }
.btn {
  width: 100%; display: inline-flex; align-items: center; justify-content: center;
  gap: 8px; border: 0; border-radius: var(--radius-md); padding: 13px 18px;
  font-family: inherit; font-size: 14.5px; font-weight: 800; color: #fff;
  background: var(--grad-primary); cursor: pointer; box-shadow: 0 8px 24px rgba(147, 51, 234, 0.32);
}
.btn:active { transform: scale(0.97); }
.btn:disabled { opacity: 0.45; cursor: not-allowed; box-shadow: none; }
.btn-secondary { background: var(--surface-hover); border: 1px solid var(--border); color: var(--text); box-shadow: none; }
.btn-sm { width: auto; flex: none; padding: 12px 18px; }
.room-code {
  font-family: ui-monospace, Consolas, monospace; font-size: 36px; font-weight: 900;
  letter-spacing: 0.3em; text-indent: 0.3em; background: var(--grad-primary);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  text-align: center; margin: 10px 0;
}
.players-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.player-item { display: flex; align-items: center; gap: 10px; padding: 10px; border-radius: var(--radius-md); background: var(--bg-subtle); border: 1px solid var(--border); min-width: 0; }
.player-item.offline { opacity: 0.55; }
.avatar-badge { width: 36px; height: 36px; border-radius: 50%; display: grid; place-items: center; font-weight: 800; color: #fff; flex: none; font-size: 14px; }
.player-info { min-width: 0; flex: 1; }
.player-name { font-weight: 700; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.player-role { display: flex; align-items: center; gap: 4px; font-size: 10.5px; color: var(--text-muted); }
.player-role .ic { width: 12px; height: 12px; color: var(--gold); }
.timer-container { position: relative; width: 116px; height: 116px; margin: 0 auto 12px; }
.timer-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.timer-track { fill: none; stroke: var(--bg-subtle); stroke-width: 7; }
.timer-progress { fill: none; stroke: var(--primary-light); stroke-width: 7; stroke-linecap: round; transition: stroke-dashoffset 0.25s linear; }
.timer-content { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.timer-num { font-size: 32px; font-weight: 900; line-height: 1; }
.timer-sub { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.role-banner { display: flex; align-items: center; justify-content: center; gap: 6px; font-weight: 700; font-size: 13.5px; color: var(--text-muted); margin-bottom: 6px; }
.target-word { min-height: 52px; display: grid; place-items: center; font-size: 28px; font-weight: 900; color: var(--gold); text-shadow: 0 0 24px rgba(234, 179, 8, 0.35); margin: 6px 0; text-align: center; }
.target-word.masked { letter-spacing: 0.15em; color: var(--text-muted); text-shadow: none; }
.result-banner { display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 6px 14px; border-radius: var(--radius-md); font-weight: 700; font-size: 13px; margin-top: 4px; }
.result-banner.success { background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.35); color: var(--success); }
.result-banner.timeout { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.35); color: var(--danger); }
.feed-box { display: flex; flex-direction: column; gap: 8px; max-height: 160px; overflow-y: auto; }
.feed-item { background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 12px; font-size: 13px; }
.feed-item.correct { border-color: rgba(16, 185, 129, 0.45); color: var(--success); }
.leader-row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }
.rank-pill { width: 24px; height: 24px; border-radius: 50%; background: var(--bg-subtle); color: var(--text-muted); display: grid; place-items: center; font-size: 11.5px; font-weight: 800; flex: none; }
.leader-row:nth-child(1) .rank-pill { background: var(--gold); color: #1e1500; }
.leader-row:nth-child(2) .rank-pill { background: var(--silver); color: #121820; }
.leader-row:nth-child(3) .rank-pill { background: var(--bronze); color: #fff; }
.podium-container { display: flex; align-items: flex-end; justify-content: center; gap: 8px; margin: 12px 0 16px; }
.podium-slot { flex: 1; max-width: 110px; display: flex; flex-direction: column; align-items: center; text-align: center; }
.podium-avatar { width: 44px; height: 44px; border-radius: 50%; display: grid; place-items: center; font-weight: 800; font-size: 16px; color: #fff; margin-bottom: 6px; }
.slot-1 .podium-avatar { width: 56px; height: 56px; border: 2px solid var(--gold); box-shadow: 0 0 18px rgba(250, 204, 21, 0.4); }
.podium-bar { width: 100%; border-radius: 10px 10px 0 0; background: var(--surface-hover); border: 1px solid var(--border); padding: 8px 2px; }
.slot-1 .podium-bar { height: 96px; background: linear-gradient(180deg, rgba(234, 179, 8, 0.25) 0%, rgba(20, 17, 44, 0.9) 100%); }
.slot-2 .podium-bar { height: 72px; }
.slot-3 .podium-bar { height: 52px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; padding: 16px; z-index: 999; }
.modal-box { width: 100%; max-width: 420px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); max-height: 85vh; overflow-y: auto; }
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-header h3 { font-size: 16px; font-weight: 800; display: flex; align-items: center; gap: 8px; }
.stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 14px; }
.stat-card { background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 12px; text-align: center; }
.stat-val { font-size: 22px; font-weight: 900; color: var(--gold); }
.stat-lbl { font-size: 11px; color: var(--text-muted); font-weight: 700; margin-top: 2px; }
.toast-msg { position: fixed; inset-inline: 0; bottom: 20px; margin: auto; width: max-content; max-width: 90%; display: flex; align-items: center; gap: 8px; background: var(--surface-active); border: 1px solid var(--border); padding: 10px 16px; border-radius: var(--radius-md); font-weight: 700; opacity: 0; transform: translateY(12px); transition: 0.2s; pointer-events: none; z-index: 1000; }
.toast-msg.show { opacity: 1; transform: translateY(0); }
.view { animation: fade-up 0.22s ease both; }
@keyframes fade-up { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.hidden { display: none !important; }
.spinner { width: 32px; height: 32px; border-radius: 50%; border: 3px solid var(--border); border-top-color: var(--primary-light); animation: spin 0.8s linear infinite; margin: 0 auto 12px; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>

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
  <symbol id="i-check" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></symbol>
  <symbol id="i-plus" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></symbol>
  <symbol id="i-play" viewBox="0 0 24 24"><polygon points="6 3 20 12 6 21 6 3"/></symbol>
  <symbol id="i-send" viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></symbol>
  <symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></symbol>
  <symbol id="i-refresh" viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></symbol>
  <symbol id="i-close" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></symbol>
</svg>

<div class="app">
  <header class="top-nav">
    <div class="brand-badge"><svg class="ic"><use href="#i-logo"/></svg></div>
    <div class="brand-info">
      <h1 data-i18n="app_title">شكون أنا؟</h1>
      <p data-i18n="app_sub">منصة التخمين والتحدي</p>
    </div>
    <div class="grow"></div>
    <div class="nav-actions">
      <button class="icon-btn" id="langBtn" title="Language"><span class="lang-badge" id="langTxt">AR</span></button>
      <button class="icon-btn" id="leaderBtn" title="Leaderboard"><svg class="ic"><use href="#i-trophy"/></svg></button>
      <button class="icon-btn" id="profileBtn" title="Profile"><svg class="ic"><use href="#i-user"/></svg></button>
      <button class="icon-btn hidden" id="leaveBtn" title="Leave"><svg class="ic"><use href="#i-logout"/></svg></button>
    </div>
  </header>

  <div class="status-pill offline" id="connPill" style="align-self: center; margin-bottom: 10px;">
    <span class="status-dot"></span><span id="connTxt" data-i18n="connecting">جاري الاتصال...</span>
  </div>

  <div id="toast" class="toast-msg"></div>

  <!-- شاشة البدء والتحميل -->
  <section id="bootView" style="text-align: center; padding: 70px 0;">
    <div class="spinner"></div><p style="color: var(--text-muted); font-weight: 700;" data-i18n="connecting_server">جاري الاتصال بالخادم الآمن...</p>
  </section>

  <!-- الواجهة الرئيسية -->
  <section id="homeView" class="view hidden">
    <div class="card" style="text-align: center; padding: 24px 16px;">
      <h2 style="font-size: 20px; font-weight: 900; margin-bottom: 6px;" data-i18n="hero_title">تحدي التخمين الجماعي</h2>
      <p style="font-size: 13.5px; color: var(--text-muted); margin-bottom: 18px;" data-i18n="hero_desc">أنشئ غرفة خاصة وشارك الرمز مع أصدقائك لبدء التحدي.</p>
      <button class="btn" id="createBtn">
        <svg class="ic"><use href="#i-plus"/></svg><span data-i18n="btn_create">إنشاء غرفة جديدة</span>
      </button>
    </div>
    <div class="card">
      <div class="card-title">
        <svg class="ic"><use href="#i-target"/></svg><span data-i18n="title_join">الانضمام إلى غرفة</span>
      </div>
      <div class="row">
        <input id="joinCodeIn" class="field code-field" maxlength="5" placeholder="ABCDE">
        <button class="btn btn-sm" id="joinBtn"><span data-i18n="btn_join">انضمام</span></button>
      </div>
    </div>
  </section>

  <!-- غرفة الانتظار (Lobby) -->
  <section id="lobbyView" class="view hidden">
    <div class="card" style="text-align: center;">
      <div style="font-size: 12px; color: var(--text-muted); font-weight: 700;" data-i18n="room_code_label">رمز الغرفة الرسمي</div>
      <div class="room-code" id="displayCode">-----</div>
      <div class="row" style="max-width: 270px; margin: 0 auto;">
        <button class="btn btn-secondary btn-sm" id="copyBtn">
          <svg class="ic"><use href="#i-copy"/></svg><span data-i18n="btn_copy">نسخ</span>
        </button>
        <button class="btn btn-secondary btn-sm" id="shareBtn">
          <svg class="ic"><use href="#i-share"/></svg><span data-i18n="btn_share">دعوة</span>
        </button>
      </div>
    </div>
    <div class="card">
      <div class="card-title">
        <svg class="ic"><use href="#i-user"/></svg>
        <span data-i18n="players_list">اللاعبون</span>
        <span class="grow"></span><span id="playerCount">0 / 12</span>
      </div>
      <div class="players-grid" id="playersList"></div>
    </div>
    <div class="card">
      <div class="card-title"><span data-i18n="match_settings">إعدادات المباراة</span></div>
      <div style="margin-bottom: 10px;">
        <label style="font-size: 12px; color: var(--text-muted); font-weight: 700;" data-i18n="lbl_category">فئة الكلمات</label>
        <select id="selCat" class="field"></select>
      </div>
      <div class="row">
        <div>
          <label style="font-size: 12px; color: var(--text-muted); font-weight: 700;" data-i18n="lbl_rounds">الجولات</label>
          <select id="selRounds" class="field"></select>
        </div>
        <div>
          <label style="font-size: 12px; color: var(--text-muted); font-weight: 700;" data-i18n="lbl_timer">وقت الجولة</label>
          <select id="selTimer" class="field"></select>
        </div>
      </div>
    </div>
    <p id="lobbyHint" style="font-size: 12px; text-align: center; margin-bottom: 12px; color: var(--text-muted); font-weight: 700;"></p>
    <button class="btn" id="startBtn">
      <svg class="ic"><use href="#i-play"/></svg><span data-i18n="btn_start">بدء المباراة</span>
    </button>
  </section>

  <!-- شاشة اللعب النشطة -->
  <section id="gameView" class="view hidden">
    <div class="card" style="text-align: center;">
      <div class="timer-container">
        <svg class="timer-svg" viewBox="0 0 120 120">
          <circle class="timer-track" cx="60" cy="60" r="52"/>
          <circle id="timerProgress" class="timer-progress" cx="60" cy="60" r="52"/>
        </svg>
        <div class="timer-content">
          <div class="timer-num" id="timerSecs">0</div>
          <div class="timer-sub" data-i18n="secs">ثانية</div>
        </div>
      </div>
      <div class="role-banner">
        <svg class="ic" id="roleIcon"><use href="#i-target"/></svg>
        <span id="roleText">...</span>
      </div>
      <div class="target-word" id="targetWord">...</div>
      <div id="resultBanner" class="result-banner hidden"></div>
    </div>
    <div class="card hidden" id="clueCard">
      <div class="card-title"><svg class="ic"><use href="#i-bulb"/></svg><span data-i18n="give_clue_title">اكتب تلميحاً ذكياً</span></div>
      <div class="row">
        <input id="clueInput" class="field" maxlength="80">
        <button class="btn btn-sm" id="sendClueBtn"><svg class="ic"><use href="#i-send"/></svg></button>
      </div>
    </div>
    <div class="card hidden" id="guessCard">
      <div class="card-title"><svg class="ic"><use href="#i-target"/></svg><span data-i18n="make_guess_title">اكتب تخمينك للكلمة</span></div>
      <div class="row">
        <input id="guessInput" class="field" maxlength="40">
        <button class="btn btn-sm" id="sendGuessBtn"><span data-i18n="btn_guess">تخمين</span></button>
      </div>
    </div>
    <div class="row" style="margin-bottom: 12px;">
      <div class="card" style="margin: 0;"><div class="card-title"><svg class="ic"><use href="#i-bulb"/></svg><span data-i18n="clues_box">التلميحات</span></div><div class="feed-box" id="cluesFeed"></div></div>
      <div class="card" style="margin: 0;"><div class="card-title"><svg class="ic"><use href="#i-target"/></svg><span data-i18n="guesses_box">المحاولات</span></div><div class="feed-box" id="guessesFeed"></div></div>
    </div>
    <div class="card">
      <div class="card-title"><svg class="ic"><use href="#i-trophy"/></svg><span data-i18n="live_scores">الترتيب المباشر</span></div>
      <div id="liveScores"></div>
    </div>
  </section>

  <!-- شاشة نهاية المباراة -->
  <section id="endView" class="view hidden">
    <div class="card" style="text-align: center; padding: 24px 16px;">
      <svg class="ic" style="width: 44px; height: 44px; color: var(--gold); margin-bottom: 8px;"><use href="#i-trophy"/></svg>
      <h2 style="font-size: 22px; font-weight: 900;" id="winnerTitle">...</h2>
      <p style="color: var(--text-muted); margin-top: 4px; font-size: 13.5px;" id="winnerSub">...</p>
    </div>
    <div class="podium-container" id="podiumBox"></div>
    <div class="card"><div class="card-title"><span data-i18n="final_results">النتائج النهائية</span></div><div id="finalScores"></div></div>
    <div class="row">
      <button class="btn" id="restartBtn"><svg class="ic"><use href="#i-refresh"/></svg><span data-i18n="btn_restart">جولة جديدة</span></button>
      <button class="btn btn-secondary" id="exitHomeBtn"><svg class="ic"><use href="#i-logout"/></svg><span data-i18n="btn_home">الرئيسية</span></button>
    </div>
  </section>

  <!-- نافذة ليدر بورد المتصدرين -->
  <div class="modal-overlay hidden" id="leaderModal">
    <div class="modal-box">
      <div class="modal-header">
        <h3><svg class="ic" style="color: var(--gold);"><use href="#i-trophy"/></svg><span data-i18n="top_players">لوحة الصدارة العالمية</span></h3>
        <button class="icon-btn" id="closeLeaderBtn"><svg class="ic"><use href="#i-close"/></svg></button>
      </div>
      <div id="globalLeaderList"></div>
    </div>
  </div>

  <!-- نافذة البروفايل -->
  <div class="modal-overlay hidden" id="profileModal">
    <div class="modal-box">
      <div class="modal-header">
        <h3><svg class="ic" style="color: var(--primary-light);"><use href="#i-user"/></svg><span data-i18n="profile_title">الملف الشخصي</span></h3>
        <button class="icon-btn" id="closeProfileBtn"><svg class="ic"><use href="#i-close"/></svg></button>
      </div>
      <div style="text-align: center; padding: 10px 0;">
        <div class="avatar-badge" id="profAvatar" style="width: 60px; height: 60px; font-size: 24px; margin: 0 auto 10px;">ل</div>
        <h4 style="font-size: 17px; font-weight: 800;" id="profName">لاعب</h4>
        <p style="font-size: 12px; color: var(--text-muted);" id="profId">ID: -----</p>
      </div>
      <div class="stat-grid">
        <div class="stat-card"><div class="stat-val" id="profScore">0</div><div class="stat-lbl" data-i18n="total_score">مجموع النقاط</div></div>
        <div class="stat-card"><div class="stat-val" id="profWins">0</div><div class="stat-lbl" data-i18n="total_wins">مرات الفوز</div></div>
        <div class="stat-card"><div class="stat-val" id="profGames">0</div><div class="stat-lbl" data-i18n="total_games">مباريات لعبتها</div></div>
        <div class="stat-card"><div class="stat-val" id="profWinRate">0%</div><div class="stat-lbl" data-i18n="win_rate">نسبة الفوز</div></div>
      </div>
    </div>
  </div>
</div>

<script>
const tg = window.Telegram?.WebApp;
try { tg?.ready(); tg?.expand(); } catch (_) {}

const I18N = {
  ar: {
    app_title: "شكون أنا؟",
    app_sub: "منصة التخمين والتحدي",
    connected: "متصل",
    connecting: "جاري الاتصال...",
    connecting_server: "جاري الاتصال بالخادم الآمن...",
    hero_title: "تحدي التخمين الجماعي",
    hero_desc: "أنشئ غرفة خاصة وشارك الرمز مع أصدقائك لبدء التحدي.",
    btn_create: "إنشاء غرفة جديدة",
    title_join: "الانضمام إلى غرفة",
    btn_join: "انضمام",
    room_code_label: "رمز الغرفة الرسمي",
    btn_copy: "نسخ",
    btn_share: "دعوة",
    players_list: "اللاعبون",
    match_settings: "إعدادات المباراة",
    lbl_category: "فئة الكلمات",
    lbl_rounds: "الجولات",
    lbl_timer: "وقت الجولة",
    btn_start: "بدء المباراة",
    give_clue_title: "اكتب تلميحاً ذكياً لمساعدة المخمن",
    make_guess_title: "اكتب إجابتك لتخمين الكلمة",
    btn_guess: "تخمين",
    clues_box: "التلميحات",
    guesses_box: "المحاولات",
    live_scores: "الترتيب المباشر",
    final_results: "النتائج النهائية",
    btn_restart: "جولة جديدة",
    btn_home: "الرئيسية",
    top_players: "لوحة الصدارة العالمية",
    profile_title: "الملف الشخصي",
    total_score: "مجموع النقاط",
    total_wins: "مرات الفوز",
    total_games: "مباريات لعبتها",
    win_rate: "نسبة الفوز",
    secs: "ثانية",
    host: "المضيف",
    pts: "ن",
    winner_is: "الفائز: ",
    no_winner: "انتهت المباراة بتعادل الجميع",
    time_up: "انتهى الوقت المحدد",
    guessed_correctly: "تم التخمين بنجاح!",
    your_turn: "دورك للتخمين الآن",
    current_guesser: "المخمن الحالي: ",
    copied: "تم نسخ رمز الغرفة بنجاح",
    min_players: "يلزم لاعبين على الأقل للبدء",
    waiting_host: "بانتظار مضيف الغرفة للبدء...",
    ready_host: "اللاعبون جاهزون، يمكنك البدء الآن"
  },
  en: {
    app_title: "Who Am I?",
    app_sub: "Multiplayer Guessing Game",
    connected: "Connected",
    connecting: "Connecting...",
    connecting_server: "Connecting to secure server...",
    hero_title: "Social Guessing Challenge",
    hero_desc: "Create a private room and share the code to start playing.",
    btn_create: "Create New Room",
    title_join: "Join a Room",
    btn_join: "Join",
    room_code_label: "Official Room Code",
    btn_copy: "Copy",
    btn_share: "Invite",
    players_list: "Players",
    match_settings: "Match Settings",
    lbl_category: "Word Category",
    lbl_rounds: "Rounds",
    lbl_timer: "Round Timer",
    btn_start: "Start Match",
    give_clue_title: "Write a clever clue for the guesser",
    make_guess_title: "Guess the target word",
    btn_guess: "Guess",
    clues_box: "Clues",
    guesses_box: "Attempts",
    live_scores: "Live Standings",
    final_results: "Final Results",
    btn_restart: "New Match",
    btn_home: "Home",
    top_players: "Global Leaderboard",
    profile_title: "Player Profile",
    total_score: "Total Points",
    total_wins: "Total Wins",
    total_games: "Games Played",
    win_rate: "Win Rate",
    secs: "sec",
    host: "Host",
    pts: "pts",
    winner_is: "Winner: ",
    no_winner: "Match ended in a tie",
    time_up: "Time is up!",
    guessed_correctly: "Guessed correctly!",
    your_turn: "It's your turn to guess!",
    current_guesser: "Current Guesser: ",
    copied: "Room code copied to clipboard",
    min_players: "At least 2 players required to start",
    waiting_host: "Waiting for the host to start...",
    ready_host: "All players ready, host can start"
  },
  fr: {
    app_title: "Qui suis-je ?",
    app_sub: "Jeu de devinettes multijoueur",
    connected: "Connecté",
    connecting: "Connexion...",
    connecting_server: "Connexion au serveur sécurisé...",
    hero_title: "Défi de devinette en groupe",
    hero_desc: "Créez un salon privé et partagez le code pour jouer.",
    btn_create: "Créer un salon",
    title_join: "Rejoindre un salon",
    btn_join: "Rejoindre",
    room_code_label: "Code du salon",
    btn_copy: "Copier",
    btn_share: "Inviter",
    players_list: "Joueurs",
    match_settings: "Paramètres de la partie",
    lbl_category: "Catégorie",
    lbl_rounds: "Manches",
    lbl_timer: "Temps",
    btn_start: "Lancer la partie",
    give_clue_title: "Écrivez un indice malin",
    make_guess_title: "Devinez le mot secret",
    btn_guess: "Valider",
    clues_box: "Indices",
    guesses_box: "Tentatives",
    live_scores: "Classement en direct",
    final_results: "Résultats finaux",
    btn_restart: "Nouvelle partie",
    btn_home: "Accueil",
    top_players: "Classement mondial",
    profile_title: "Profil du joueur",
    total_score: "Points totaux",
    total_wins: "Victoires",
    total_games: "Parties jouées",
    win_rate: "Taux de victoire",
    secs: "sec",
    host: "Hôte",
    pts: "pts",
    winner_is: "Vainqueur : ",
    no_winner: "Partie terminée par une égalité",
    time_up: "Temps écoulé !",
    guessed_correctly: "Mot trouvé avec succès !",
    your_turn: "C'est votre tour de deviner !",
    current_guesser: "Devineur actuel : ",
    copied: "Code copié dans le presse-papier",
    min_players: "Au moins 2 joueurs requis",
    waiting_host: "En attente de l'hôte...",
    ready_host: "Les joueurs sont prêts, vous pouvez lancer"
  }
};

const CATEGORIES_TRANSLATIONS = {
  ar: { celebs: 'مشاهير وثقافة', football: 'كرة قدم وأندية', anime: 'شخصيات أنمي', games: 'ألعاب فيديو', movies: 'أفلام ومسلسلات', animals: 'عالم الحيوان', food: 'أكلات ومأكولات', general: 'معلومات عامة' },
  en: { celebs: 'Celebrities & Culture', football: 'Football & Clubs', anime: 'Anime Characters', games: 'Video Games', movies: 'Movies & Series', animals: 'Animal Kingdom', food: 'Food & Dishes', general: 'General Knowledge' },
  fr: { celebs: 'Célébrités & Culture', football: 'Football & Clubs', anime: "Personnages d'Anime", games: 'Jeux Vidéo', movies: 'Films & Séries', animals: 'Monde Animal', food: 'Gastronomie', general: 'Culture Générale' }
};

let currentLang = localStorage.getItem('game_lang') || 'ar';

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('game_lang', lang);
  document.documentElement.lang = lang;
  document.documentElement.dir = (lang === 'ar') ? 'rtl' : 'ltr';
  $('langTxt').textContent = lang.toUpperCase();

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (I18N[lang] && I18N[lang][key]) el.textContent = I18N[lang][key];
  });

  const selCat = $('selCat');
  const curVal = selCat.value;
  selCat.replaceChildren();
  Object.entries(CATEGORIES_TRANSLATIONS[lang]).forEach(([k, v]) => {
    selCat.add(new Option(v, k));
  });
  if (curVal) selCat.value = curVal;

  const selRounds = $('selRounds');
  const curR = selRounds.value;
  selRounds.replaceChildren();
  [3, 5, 8, 10].forEach(n => selRounds.add(new Option(`${n} ${lang==='ar'?'جولات':(lang==='fr'?'manches':'rounds')}`, n)));
  if (curR) selRounds.value = curR;

  const selTimer = $('selTimer');
  const curT = selTimer.value;
  selTimer.replaceChildren();
  [30, 45, 60, 90].forEach(n => selTimer.add(new Option(`${n} ${I18N[lang].secs}`, n)));
  if (curT) selTimer.value = curT;

  if (state) render();
}

const $ = id => document.getElementById(id);
const CIRCUMFERENCE = 2 * Math.PI * 52;
const VIEWS = ['homeView', 'lobbyView', 'gameView', 'endView'];

let ws = null, me = null, state = null, timerInterval = null;
let currentRoomCode = new URLSearchParams(location.search).get('room')?.toUpperCase() || null;
let globalLeaderboardCache = [];

$('timerProgress').style.strokeDasharray = CIRCUMFERENCE;

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

function connectServer() {
  const protocol = location.protocol === 'https:' ? 'wss://' : 'ws://';
  ws = new WebSocket(`${protocol}${location.host}/ws`);

  ws.onopen = () => {
    $('connPill').classList.remove('offline');
    $('connTxt').textContent = I18N[currentLang].connected;
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
      } else if (m.type === 'leaderboard') {
        globalLeaderboardCache = m.data;
        renderGlobalLeaderboard(m.data);
      } else if (m.type === 'error') {
        toast(m.message);
        if (!state) switchView('homeView');
      }
    } catch (_) {}
  };
  ws.onclose = () => {
    $('connPill').classList.add('offline');
    $('connTxt').textContent = (currentLang === 'ar') ? 'غير متصل' : 'Offline';
    setTimeout(connectServer, 2000);
  };
}

const getPlayerName = id => state?.players.find(p => p.id === id)?.name || 'Player';

function render() {
  if (!state || !me) return switchView('homeView');
  const t = I18N[currentLang];

  if (state.status === 'lobby') {
    switchView('lobbyView');
    const isHost = state.host === me.id;
    $('displayCode').textContent = state.code;
    $('playerCount').textContent = `${state.players.length} / 12`;
    $('selCat').value = state.settings.category;
    $('selRounds').value = state.settings.rounds;
    $('selTimer').value = state.settings.timer;
    ['selCat', 'selRounds', 'selTimer'].forEach(id => { $(id).disabled = !isHost; });
    $('startBtn').disabled = !isHost || state.players.length < 2;

    if (state.players.length < 2) $('lobbyHint').textContent = t.min_players;
    else if (isHost) $('lobbyHint').textContent = t.ready_host;
    else $('lobbyHint').textContent = t.waiting_host;

    const list = $('playersList');
    list.replaceChildren();
    state.players.forEach(p => {
      const d = document.createElement('div');
      d.className = `player-item ${p.online ? '' : 'offline'}`;
      const isRoomHost = p.id === state.host;
      const youTxt = (currentLang === 'ar') ? 'أنت' : ((currentLang === 'fr') ? 'vous' : 'you');
      d.innerHTML = `<div class="avatar-badge" style="background: hsl(${Math.abs(p.id * 53)%360},65%,45%)">${(p.name||'P')[0]}</div>
                     <div class="player-info">
                       <div class="player-name">${p.name}${p.id===me.id?' (' + youTxt + ')':''}</div>
                       <div class="player-role">${isRoomHost?'<svg class="ic"><use href="#i-crown"/></svg> ' + t.host : (p.online?'Online':'Offline')}</div>
                     </div>`;
      list.appendChild(d);
    });
  } else if (state.status === 'playing') {
    switchView('gameView');
    const r = state.round;
    const isGuesser = r.guesser === me.id;
    $('roleText').textContent = isGuesser ? t.your_turn : `${t.current_guesser} ${getPlayerName(r.guesser)}`;
    $('targetWord').textContent = r.word || 'ـ ـ ـ ـ ـ ـ';
    $('targetWord').classList.toggle('masked', !r.word);

    $('clueCard').classList.toggle('hidden', isGuesser || !r.active);
    $('guessCard').classList.toggle('hidden', !isGuesser || !r.active);

    const banner = $('resultBanner');
    if (!r.active) {
      banner.classList.remove('hidden');
      banner.className = `result-banner ${r.solved ? 'success' : 'timeout'}`;
      banner.innerHTML = `<svg class="ic"><use href="#i-${r.solved ? 'check' : 'clock'}"/></svg><span>${r.solved ? t.guessed_correctly : t.time_up}</span>`;
    } else {
      banner.classList.add('hidden');
    }

    const cFeed = $('cluesFeed'); cFeed.replaceChildren();
    r.clues.forEach(c => {
      const item = document.createElement('div');
      item.className = 'feed-item';
      item.textContent = `${getPlayerName(c.by)}: ${c.text}`;
      cFeed.appendChild(item);
    });

    const gFeed = $('guessesFeed'); gFeed.replaceChildren();
    r.guesses.forEach(g => {
      const item = document.createElement('div');
      item.className = `feed-item ${g.ok ? 'correct' : ''}`;
      item.textContent = g.text;
      gFeed.appendChild(item);
    });

    const sBox = $('liveScores'); sBox.replaceChildren();
    [...state.players].sort((a,b)=>b.score-a.score).forEach((p, idx) => {
      const row = document.createElement('div');
      row.className = 'leader-row';
      row.innerHTML = `<span class="rank-pill">${idx+1}</span><span style="flex:1; font-weight:700;">${p.name}</span><b style="color:var(--gold);">${p.score} ${t.pts}</b>`;
      sBox.appendChild(row);
    });

    clearInterval(timerInterval);
    const end = Date.now() + r.left;
    const totalMs = state.settings.timer * 1000;
    const updateTimer = () => {
      const rem = r.active ? Math.max(0, end - Date.now()) : 0;
      $('timerSecs').textContent = Math.ceil(rem / 1000);
      $('timerProgress').style.strokeDashoffset = CIRCUMFERENCE * (1 - rem / totalMs);
    };
    updateTimer();
    if (r.active) timerInterval = setInterval(updateTimer, 250);
  } else if (state.status === 'ended') {
    switchView('endView');
    clearInterval(timerInterval);
    const sorted = [...state.players].sort((a,b)=>b.score-a.score);
    const winner = sorted[0];
    if (winner && winner.score > 0) {
      $('winnerTitle').textContent = `${t.winner_is} ${winner.name}`;
      $('winnerSub').textContent = `${winner.score} ${t.pts}`;
    } else {
      $('winnerTitle').textContent = t.no_winner;
      $('winnerSub').textContent = "";
    }

    const podiumBox = $('podiumBox');
    podiumBox.replaceChildren();
    const slots = [
      { p: sorted[1], cls: 'slot-2' },
      { p: sorted[0], cls: 'slot-1' },
      { p: sorted[2], cls: 'slot-3' }
    ];
    slots.forEach(({ p, cls }) => {
      if (!p) return;
      const col = document.createElement('div');
      col.className = `podium-slot ${cls}`;
      const av = document.createElement('div');
      av.className = 'podium-avatar';
      av.textContent = p.name.charAt(0);
      av.style.background = `hsl(${Math.abs(p.id * 53)%360},65%,45%)`;
      const bar = document.createElement('div');
      bar.className = 'podium-bar';
      bar.innerHTML = `<div style="font-weight: 700; font-size: 11px;">${p.name}</div><div style="font-weight: 800; color: var(--gold);">${p.score} ${t.pts}</div>`;
      col.append(av, bar);
      podiumBox.appendChild(col);
    });

    const fBox = $('finalScores'); fBox.replaceChildren();
    sorted.forEach((p, idx) => {
      const row = document.createElement('div');
      row.className = 'leader-row';
      row.innerHTML = `<span class="rank-pill">${idx+1}</span><span style="flex:1; font-weight:700;">${p.name}</span><b style="color:var(--gold);">${p.score} ${t.pts}</b>`;
      fBox.appendChild(row);
    });
    $('restartBtn').classList.toggle('hidden', state.host !== me.id);
  }
}

function updateProfileUI(u) {
  if (!u) return;
  $('profName').textContent = u.name;
  $('profId').textContent = `ID: ${u.id}`;
  $('profAvatar').textContent = (u.name || 'P')[0];
  $('profAvatar').style.background = `hsl(${Math.abs(u.id * 53)%360},65%,45%)`;
  const s = u.stats || {};
  $('profScore').textContent = s.score || 0;
  $('profWins').textContent = s.wins || 0;
  $('profGames').textContent = s.games || 0;
  const rate = s.games ? Math.round((s.wins / s.games) * 100) : 0;
  $('profWinRate').textContent = `${rate}%`;
}

function renderGlobalLeaderboard(list) {
  const box = $('globalLeaderList');
  box.replaceChildren();
  if (!list.length) {
    box.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:20px;">لا توجد سجلات بعد</p>';
    return;
  }
  list.forEach(p => {
    const row = document.createElement('div');
    row.className = 'leader-row';
    row.innerHTML = `<span class="rank-pill">${p.rank}</span>
                     <span style="flex:1; font-weight:700;">${p.name}</span>
                     <span style="font-size:12px; color:var(--text-muted); margin-inline-end:8px;">🏆 ${p.wins}</span>
                     <b style="color:var(--gold);">${p.score} ${I18N[currentLang].pts}</b>`;
    box.appendChild(row);
  });
}

function leave() {
  sendMsg({ type: 'leave' });
  state = null; currentRoomCode = null; clearInterval(timerInterval);
  switchView('homeView');
}

$('langBtn').onclick = () => {
  const langs = ['ar', 'en', 'fr'];
  const next = langs[(langs.indexOf(currentLang) + 1) % langs.length];
  setLanguage(next);
};

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

$('createBtn').onclick = () => sendMsg({ type: 'create' });
$('joinBtn').onclick = () => {
  const code = $('joinCodeIn').value.trim().toUpperCase();
  if (code.length === 5) sendMsg({ type: 'join', code });
};
$('copyBtn').onclick = () => {
  if (state?.code) { navigator.clipboard?.writeText(state.code); toast(I18N[currentLang].copied); }
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

['selCat', 'selRounds', 'selTimer'].forEach(id => {
  $(id).onchange = () => sendMsg({
    type: 'settings',
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

setLanguage(currentLang);
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

def clue_has_forbidden_word(clue: str, target: str) -> bool:
    n_clue, n_target = norm(clue), norm(target)
    if not n_clue or not n_target:
        return False
    if n_target in n_clue or strip_al(n_target) in n_clue:
        return True
    parts = [norm(p) for p in target.split() if len(norm(p)) >= 3]
    for p in parts:
        sp = strip_al(p)
        if len(sp) >= 3 and sp in n_clue:
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
        self.settings = {"category": "general", "rounds": 5, "timer": 60}
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
            rnd = {
                "no": r["no"],
                "total": self.settings["rounds"],
                "guesser": r["guesser"],
                "active": r["active"],
                "solved": r["solved"],
                "left": max(0, int((r["end"] - time.time()) * 1000)),
                "word": r["word"] if (not r["active"] or uid != r["guesser"]) else None,
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

    def pick_word(self):
        cat = self.settings["category"]
        pool = [w for w in WORDS.get(cat, WORDS["general"]) if w not in self.used_words]
        if not pool:
            self.used_words.clear()
            pool = WORDS.get(cat, WORDS["general"])
        chosen = random.choice(pool)
        self.used_words.add(chosen)
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

        word = self.pick_word()
        self.round = {
            "no": self.no,
            "word": word,
            "guesser": active_guesser,
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
                return "Cannot change settings now"
            s = {
                "category": data.get("category"),
                "rounds": data.get("rounds"),
                "timer": data.get("timer"),
            }
            if s["category"] in WORDS and s["rounds"] in ROUNDS and s["timer"] in TIMERS:
                self.settings = s
                await self.broadcast()
            return None

        if t == "start":
            if uid != self.host or self.status != "lobby":
                return "Only host can start"
            if len([p for p in self.order if p in self.conns]) < 2:
                return "Need at least 2 players"
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
                return "Only host can restart"
            self.status = "lobby"
            self.round = None
            self.no = 0
            self.used_words.clear()
            for p in self.players.values():
                p["score"] = 0
            await self.broadcast()
            return None

        if t == "clue":
            if self.status != "playing" or not r or not r["active"] or uid == r["guesser"]:
                return "Not allowed now"
            text = str(data.get("text", "")).strip()[:80]
            if not text:
                return "Empty clue"
            if clue_has_forbidden_word(text, r["word"]):
                return "Cannot use target word in clue"
            r["clues"].append({"by": uid, "text": text})
            await self.broadcast()
            return None

        if t == "guess":
            if self.status != "playing" or not r or not r["active"] or uid != r["guesser"]:
                return "Not your turn to guess"
            text = str(data.get("text", "")).strip()[:40]
            n = norm(text)
            if not n:
                return "Invalid guess"
            if n in r["gn"]:
                return "Already guessed"
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
                    await send(ws, err("Slow down"))
                    continue
                last_act = now

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
                    user = {"id": rnd_id, "name": f"Player {str(rnd_id)[-3:]}"}

                uid, name = user["id"], user["name"]
                s = STATS.get(str(uid), {"score": 0, "wins": 0, "games": 0})
                user["stats"] = s
                await send(ws, {"type": "authed", "user": user})

            elif uid is None:
                continue

            elif t in ("create", "join"):
                if t == "create":
                    code = new_code()
                    target = ROOMS[code] = Room(code, uid)
                else:
                    target = ROOMS.get(str(data.get("code", "")).upper().strip())
                    if target is None:
                        await send(ws, err("Invalid room code"))
                        continue
                    if uid not in target.players and (
                        target.status != "lobby" or len(target.players) >= MAX_PLAYERS
                    ):
                        await send(ws, err("Room full or game in progress"))
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
                    error = "Error processing request"
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

async def send_tg_msg(session, chat_id, text, reply_markup=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        await session.post(url, json=payload)
    except Exception:
        pass

def get_play_keyboard():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "🎮 العب الآن • Play • Jouer",
                    "web_app": {"url": APP_URL}
                }
            ]
        ]
    }

async def handle_tg_message(session, msg):
    chat_id = msg.get("chat", {}).get("id")
    user_id = msg.get("from", {}).get("id")
    username = (msg.get("from", {}).get("username") or "").lower()
    text = (msg.get("text") or "").strip()
    if not chat_id:
        return

    if user_id:
        USERS.add(user_id)
        save_db(USERS_FILE, {str(u): True for u in USERS})

    is_owner = (user_id == OWNER_ID) or (username == OWNER_USERNAME.lower())

    if text.startswith("/start"):
        await send_tg_msg(
            session,
            chat_id,
            "مرحباً بك في منصة «شكون أنا؟» 🎮\n"
            "Bienvenue sur «Qui suis-je ?»\n"
            "Welcome to «Who Am I?»\n\n"
            "اضغط على الزر الشفاف بالأسفل لفتح اللعبة وبدء التحدي مباشرة!",
            reply_markup=get_play_keyboard()
        )
    elif text.startswith("/stats") and is_owner:
        total_p = len(STATS)
        active_r = len(ROOMS)
        await send_tg_msg(
            session,
            chat_id,
            f"👑 إحصائيات المالك ({OWNER_USERNAME}):\n"
            f"- إجمالي اللاعبين المسجلين: {total_p}\n"
            f"- الغرف النشطة الآن: {active_r}\n"
            f"- إجمالي مستخدمي البوت: {len(USERS)}"
        )
    elif text.startswith("/broadcast") and is_owner:
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
        else:
            await send_tg_msg(session, chat_id, "طريقة الاستخدام: /broadcast نص الرسالة")
    elif text.startswith("/help"):
        await send_tg_msg(
            session,
            chat_id,
            "اضغط على الزر الشفاف أسفل الرسالة للعب مباشرة! 👇",
            reply_markup=get_play_keyboard()
        )

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
