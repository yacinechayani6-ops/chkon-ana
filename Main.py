"""
شكون أنا؟ - Who Am I? - Qui suis-je?
النسخة الشاملة الخالية من الإيموجيز مع فتح التطبيق داخل تيليجرام فقط في المجموعات.
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

BOT_TOKEN = os.getenv("BOT_TOKEN", "9269122102:AAFxKUbT6Bw4_lIfLWVenBDTWQ1M9_fGzMA")
BOT_USERNAME = "chkonanabot"
APP_URL = "https://chkon-ana.onrender.com/"
OWNER_USERNAME = "IIlIlIlllIIllIIl"
OWNER_ID = 8684495458
PORT = int(os.getenv("PORT", "8080"))

STATS_FILE = Path(__file__).parent / "stats.json"
USERS_FILE = Path(__file__).parent / "users.json"
BANNED_FILE = Path(__file__).parent / "banned.json"
CUSTOM_WORDS_FILE = Path(__file__).parent / "custom_words.json"

ROUNDS = (3, 5, 8, 10)
TIMERS = (30, 45, 60, 90)
MAX_PLAYERS = 12

GROUP_ROOMS = {}

WORDS_DATA = {
    "celebs": [
        {"word": "الشاب خالد", "taboo": ["دي دي", "مغني", "وهران"]},
        {"word": "زين الدين زيدان", "taboo": ["فرنسا", "ريال مدريد", "نطحة"]},
        {"word": "الشاب حسني", "taboo": ["راي", "عاطفي", "مرحوم"]},
        {"word": "عثمان عريوات", "taboo": ["كرنفال في دشرة", "ممثل", "بوعمامة"]},
        {"word": "صالح أوقروت", "taboo": ["عاشور العاشر", "جمعي فاملي", "صويلح"]},
        {"word": "لخضر بلومي", "taboo": ["رقم 10", "كعب", "المانيا"]},
        {"word": "سولكينغ", "taboo": ["غناء", "راب", "فرنسا"]},
        {"word": "وردة الجزائرية", "taboo": ["بتونس بيك", "مصر", "طرب"]},
        {"word": "دحمان الحراشي", "taboo": ["يا الرايح", "شعبي", "مندول"]},
        {"word": "مفدي زكريا", "taboo": ["قسما", "شاعر", "النشيد"]},
        {"word": "العربي بن مهيدي", "taboo": ["ابتسامة", "شهيد", "ثورة"]},
        {"word": "بيونة", "taboo": ["ممثلة", "ناس ملاح", "كوميديا"]},
        {"word": "الشاب مامي", "taboo": ["أمير الراي", "ستينغ", "سعيدة"]},
        {"word": "محمد فلاق", "taboo": ["مسرح", "فكاهة", "فرنسا"]}
    ],
    "football": [
        {"word": "رياض محرز", "taboo": ["سيتي", "أهلي", "يسارية"]},
        {"word": "ليونيل ميسي", "taboo": ["أرجنتين", "برشلونة", "كرة ذهبية"]},
        {"word": "كريستيانو رونالدو", "taboo": ["نصر", "برتغال", "ريال مدريد"]},
        {"word": "محمد صلاح", "taboo": ["مصر", "ليفربول", "فخر العرب"]},
        {"word": "إسماعيل بن ناصر", "taboo": ["ميلان", "وسط", "محارب"]},
        {"word": "يوسف بلايلي", "taboo": ["مراوغ", "مولودية", "ترجي"]},
        {"word": "إسلام سليماني", "taboo": ["هداف", "رأسيات", "سبورتينغ"]},
        {"word": "بغداد بونجاح", "taboo": ["سد", "هدف القاهرة", "شمال"]},
        {"word": "كيليان مبابي", "taboo": ["باريس", "فرنسا", "ريال مدريد"]},
        {"word": "إيرلينغ هالاند", "taboo": ["مانشستر سيتي", "نرويج", "أهداف"]},
        {"word": "كريم بنزيما", "taboo": ["اتحاد", "حكومة", "ريال مدريد"]},
        {"word": "مولودية الجزائر", "taboo": ["عميد", "شنوة", "5 جويلية"]},
        {"word": "شبيبة القبائل", "taboo": ["كناري", "تيزي وزو", "ألقاب"]},
        {"word": "ريال مدريد", "taboo": ["برنابيو", "أبطال أوروبا", "أبيض"]},
        {"word": "برشلونة", "taboo": ["كامب نو", "كتالونيا", "ميسي"]}
    ],
    "anime": [
        {"word": "ناروتو", "taboo": ["نينجا", "ساسكي", "هوكاجي"]},
        {"word": "لوفي", "taboo": ["قبعة القش", "ون بيس", "مطاط"]},
        {"word": "غوكو", "taboo": ["دراغون بول", "سايان", "كاميهاميها"]},
        {"word": "كونان", "taboo": ["متحري", "تقلص", "سينشي"]},
        {"word": "ليفاي", "taboo": ["هجوم العمالقة", "قائد", "نظافة"]},
        {"word": "إيرين ييغر", "taboo": ["عملاق", "حرية", "تيتان"]},
        {"word": "ساسكي", "taboo": ["شارينغان", "أوتشيها", "انتقام"]},
        {"word": "تانجيرو", "taboo": ["قاتل الشياطين", "نيزوكو", "سيف"]},
        {"word": "ساتورو غوجو", "taboo": ["عيون زرقاء", "عصابة", "إنفينيتي"]},
        {"word": "سايتاما", "taboo": ["لكمة واحدة", "أصلع", "بطل"]}
    ],
    "food": [
        {"word": "الشخشوخة", "taboo": ["بسكرة", "حار", "مرقة"]},
        {"word": "الكسكسي", "taboo": ["جمعة", "طعام", "خضار"]},
        {"word": "المحجوبة", "taboo": ["بصل", "حار", "فرينة"]},
        {"word": "الكرنتيكا", "taboo": ["حمص", "وهران", "كمون"]},
        {"word": "البوراك", "taboo": ["رمضان", "ديول", "بطاطا"]},
        {"word": "الرشتة", "taboo": ["عاصمة", "لفت", "قرفة"]},
        {"word": "الشربة فريك", "taboo": ["رمضان", "لحم", "دبشة"]},
        {"word": "طاجين الزيتون", "taboo": ["جزر", "مرقة صفراء", "فطر"]},
        {"word": "المسمن", "taboo": ["معارك", "عسل", "قهوة"]},
        {"word": "البقلاوة", "taboo": ["جوز", "عسل", "ورقات"]},
        {"word": "المقروط", "taboo": ["غرس", "تمر", "مقلي"]},
        {"word": "قلب اللوز", "taboo": ["شاربات", "صينية", "رمضان"]}
    ],
    "games": [
        {"word": "ماينكرافت", "taboo": ["بلوكات", "كريبر", "بناء"]},
        {"word": "فورتنايت", "taboo": ["باتل رويال", "رقصات", "بناء"]},
        {"word": "فيفا", "taboo": ["كرة قدم", "إي إيه", "ألتيميت"]},
        {"word": "ببجي", "taboo": ["طائرة", "خوذة", "دجاجة"]},
        {"word": "غراند ثفت أوتو", "taboo": ["سرقة", "سيارات", "جي تي أي"]},
        {"word": "ليغ أوف ليجيندز", "taboo": ["موبا", "أبطال", "رايوت"]},
        {"word": "فالورانت", "taboo": ["طلقات", "سبايك", "قدرات"]},
        {"word": "كول أوف ديوتي", "taboo": ["حرب", "سلاح", "زومبي"]},
        {"word": "أمونغ آس", "taboo": ["سفينة", "مندس", "تصويت"]},
        {"word": "كلاش أوف كلانس", "taboo": ["قرية", "هجوم", "جواهر"]}
    ],
    "general": [
        {"word": "برج إيفل", "taboo": ["باريس", "فرنسا", "حديد"]},
        {"word": "الأهرامات", "taboo": ["مصر", "فراعنة", "مثلث"]},
        {"word": "الإنترنت", "taboo": ["شبكة", "ويفي", "مواقع"]},
        {"word": "الذكاء الاصطناعي", "taboo": ["روبوت", "حاسوب", "تفكير"]},
        {"word": "السيارة", "taboo": ["عجلات", "سياقة", "محرك"]},
        {"word": "القمر", "taboo": ["ليل", "فضاء", "سماء"]},
        {"word": "الأوكسجين", "taboo": ["تنفس", "هواء", "غاز"]},
        {"word": "الكهرباء", "taboo": ["ضوء", "طاقة", "أسلاك"]},
        {"word": "الصحراء الكبرى", "taboo": ["رمل", "جمال", "حرارة"]},
        {"word": "البوصلة", "taboo": ["اتجاه", "شمال", "مغناطيس"]},
        {"word": "الطائرة", "taboo": ["مطار", "أجنحة", "سفر"]},
        {"word": "البركان", "taboo": ["حمم", "نار", "جبل"]}
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

custom_words = load_db(CUSTOM_WORDS_FILE)
for cat, items in custom_words.items():
    if cat in WORDS_DATA and isinstance(items, list):
        WORDS_DATA[cat].extend(items)

STATS = load_db(STATS_FILE)
USERS = set(int(u) for u in load_db(USERS_FILE).keys() if str(u).isdigit())
BANNED_USERS = set(load_db(BANNED_FILE).keys())

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
  --border: rgba(168, 85, 247, 0.18);
  --border-focus: rgba(168, 85, 247, 0.45);
  --text: #f8f7ff;
  --text-muted: #948fb3;
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
  overflow-x: hidden;
  -webkit-tap-highlight-color: transparent;
}
html[dir="ltr"] body { font-family: "Inter", "Cairo", system-ui, sans-serif; }
.sprite { position: absolute; width: 0; height: 0; overflow: hidden; }
.ic { width: 19px; height: 19px; flex: none; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; display: inline-block; vertical-align: middle; }
.app { max-width: 480px; margin: 0 auto; min-height: 100vh; display: flex; flex-direction: column; padding: 14px; position: relative; }
.top-nav { display: flex; align-items: center; gap: 8px; padding: 6px 0 14px; }
.brand-badge { width: 38px; height: 38px; border-radius: 12px; background: var(--grad-primary); display: grid; place-items: center; color: #fff; box-shadow: 0 8px 20px rgba(147, 51, 234, 0.35); }
.brand-info h1 { font-size: 16px; font-weight: 800; letter-spacing: -0.2px; }
.brand-info p { font-size: 11px; color: var(--text-muted); }
.grow { flex: 1; }
.nav-actions { display: flex; align-items: center; gap: 6px; }
.status-pill { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 700; padding: 4px 8px; border-radius: 99px; background: var(--surface); border: 1px solid var(--border); color: var(--text-muted); }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--success); }
.status-pill.offline .status-dot { background: var(--danger); }
.icon-btn { width: 36px; height: 36px; border-radius: 11px; border: 1px solid var(--border); background: var(--surface); color: var(--text); display: grid; place-items: center; cursor: pointer; transition: transform 0.12s, background 0.15s; }
.icon-btn:active { transform: scale(0.92); }
.card { background: var(--grad-surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; margin-bottom: 12px; backdrop-filter: blur(14px); }
.card-title { display: flex; align-items: center; gap: 8px; font-size: 13.5px; font-weight: 700; color: var(--text-muted); margin-bottom: 12px; }
.card-title .ic { color: var(--primary-light); }
.field { width: 100%; font-family: inherit; font-size: 14px; color: var(--text); background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 12px 14px; outline: none; }
.field:focus { border-color: var(--border-focus); box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.2); }
.code-field { text-align: center; letter-spacing: 0.25em; font-family: monospace; font-weight: 800; font-size: 18px; text-transform: uppercase; }
.row { display: flex; gap: 8px; }
.row > * { flex: 1; min-width: 0; }
.btn { width: 100%; display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 0; border-radius: var(--radius-md); padding: 13px 18px; font-family: inherit; font-size: 14.5px; font-weight: 800; color: #fff; background: var(--grad-primary); cursor: pointer; box-shadow: 0 8px 24px rgba(147, 51, 234, 0.32); }
.btn:active { transform: scale(0.97); }
.btn-secondary { background: var(--surface-hover); border: 1px solid var(--border); color: var(--text); box-shadow: none; }
.btn-sm { width: auto; flex: none; padding: 12px 18px; }
.room-code { font-family: monospace; font-size: 36px; font-weight: 900; letter-spacing: 0.3em; text-indent: 0.3em; background: var(--grad-primary); -webkit-background-clip: text; background-clip: text; color: transparent; text-align: center; margin: 10px 0; }
.players-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.player-item { display: flex; align-items: center; gap: 10px; padding: 10px; border-radius: var(--radius-md); background: var(--bg-subtle); border: 1px solid var(--border); min-width: 0; }
.avatar-box { width: 38px; height: 38px; border-radius: 50%; overflow: hidden; display: grid; place-items: center; font-weight: 800; color: #fff; flex: none; font-size: 14px; position: relative; border: 2px solid var(--border); }
.avatar-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.player-info { min-width: 0; flex: 1; }
.player-name { font-weight: 700; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.player-role { display: flex; align-items: center; gap: 4px; font-size: 10.5px; color: var(--text-muted); }
.timer-container { position: relative; width: 116px; height: 116px; margin: 0 auto 12px; }
.timer-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.timer-track { fill: none; stroke: var(--bg-subtle); stroke-width: 7; }
.timer-progress { fill: none; stroke: var(--primary-light); stroke-width: 7; stroke-linecap: round; transition: stroke-dashoffset 0.25s linear; }
.timer-content { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.timer-num { font-size: 32px; font-weight: 900; line-height: 1; }
.timer-sub { font-size: 11px; color: var(--text-muted); }
.role-banner { display: flex; align-items: center; justify-content: center; gap: 6px; font-weight: 700; font-size: 13.5px; color: var(--text-muted); margin-bottom: 6px; }
.target-word { min-height: 52px; display: grid; place-items: center; font-size: 28px; font-weight: 900; color: var(--gold); text-shadow: 0 0 24px rgba(234, 179, 8, 0.35); margin: 6px 0; text-align: center; }
.target-word.masked { letter-spacing: 0.15em; color: var(--text-muted); text-shadow: none; }
.taboo-tag { display: inline-block; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: var(--danger); padding: 4px 10px; border-radius: 99px; font-size: 12px; font-weight: 700; margin: 2px; }
.result-banner { display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 6px 14px; border-radius: var(--radius-md); font-weight: 700; font-size: 13px; margin-top: 4px; }
.result-banner.success { background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.35); color: var(--success); }
.result-banner.timeout { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.35); color: var(--danger); }
.feed-box { display: flex; flex-direction: column; gap: 8px; max-height: 150px; overflow-y: auto; }
.feed-item { background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 12px; font-size: 13px; }
.feed-item.correct { border-color: rgba(16, 185, 129, 0.45); color: var(--success); }
.leader-row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }
.rank-pill { width: 24px; height: 24px; border-radius: 50%; background: var(--bg-subtle); color: var(--text-muted); display: grid; place-items: center; font-size: 11.5px; font-weight: 800; flex: none; }
.leader-row:nth-child(1) .rank-pill { background: var(--gold); color: #1e1500; }
.leader-row:nth-child(2) .rank-pill { background: var(--silver); color: #121820; }
.leader-row:nth-child(3) .rank-pill { background: var(--bronze); color: #fff; }
.podium-container { display: flex; align-items: flex-end; justify-content: center; gap: 8px; margin: 12px 0 16px; }
.podium-slot { flex: 1; max-width: 110px; display: flex; flex-direction: column; align-items: center; text-align: center; }
.podium-avatar { width: 48px; height: 48px; border-radius: 50%; overflow: hidden; display: grid; place-items: center; font-weight: 800; font-size: 16px; color: #fff; margin-bottom: 6px; border: 2px solid transparent; }
.slot-1 .podium-avatar { width: 60px; height: 60px; border-color: var(--gold); box-shadow: 0 0 18px rgba(250, 204, 21, 0.4); }
.podium-bar { width: 100%; border-radius: 10px 10px 0 0; background: var(--surface-hover); border: 1px solid var(--border); padding: 8px 2px; }
.slot-1 .podium-bar { height: 96px; background: linear-gradient(180deg, rgba(234, 179, 8, 0.25) 0%, rgba(20, 17, 44, 0.9) 100%); }
.slot-2 .podium-bar { height: 72px; }
.slot-3 .podium-bar { height: 52px; }
.reactions-bar { display: flex; justify-content: center; gap: 8px; margin-top: 10px; padding: 8px; background: var(--bg-subtle); border-radius: var(--radius-md); border: 1px solid var(--border); }
.react-btn { width: 38px; height: 38px; border-radius: 10px; border: 1px solid var(--border); background: var(--surface); color: var(--text); display: grid; place-items: center; cursor: pointer; transition: transform 0.15s; }
.react-btn:active { transform: scale(1.2); }
.flying-reaction { position: fixed; bottom: 80px; width: 34px; height: 34px; color: var(--gold); pointer-events: none; animation: flyUp 1.8s ease-out forwards; z-index: 9999; }
@keyframes flyUp { 0% { opacity: 1; transform: translateY(0) scale(0.6); } 100% { opacity: 0; transform: translateY(-380px) scale(1.4); } }
.badge-pill { display: inline-block; font-size: 10.5px; font-weight: 800; padding: 2px 8px; border-radius: 99px; background: rgba(234, 179, 8, 0.15); color: var(--gold); border: 1px solid rgba(234, 179, 8, 0.3); }
.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; padding: 16px; z-index: 999; }
.modal-box { width: 100%; max-width: 420px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; max-height: 85vh; overflow-y: auto; }
.stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 14px; }
.stat-card { background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 12px; text-align: center; }
.stat-val { font-size: 22px; font-weight: 900; color: var(--gold); }
.stat-lbl { font-size: 11px; color: var(--text-muted); font-weight: 700; margin-top: 2px; }
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
  <symbol id="i-sound" viewBox="0 0 24 24"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></symbol>
  <symbol id="i-mute" viewBox="0 0 24 24"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></symbol>
  <symbol id="i-close" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></symbol>
  <symbol id="i-zap" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></symbol>
  <symbol id="i-thumbs-up" viewBox="0 0 24 24"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></symbol>
  <symbol id="i-flame" viewBox="0 0 24 24"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></symbol>
  <symbol id="i-smile" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></symbol>
  <symbol id="i-help" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></symbol>
</svg>

<div class="app">
  <header class="top-nav">
    <div class="brand-badge"><svg class="ic"><use href="#i-logo"/></svg></div>
    <div style="margin-inline-start: 8px;">
      <h1 data-i18n="app_title">شكون أنا؟</h1>
      <p data-i18n="app_sub">منصة التخمين والتحدي</p>
    </div>
    <div class="grow"></div>
    <div class="nav-actions">
      <button class="icon-btn" id="soundBtn"><svg class="ic"><use href="#i-sound"/></svg></button>
      <button class="icon-btn" id="langBtn"><span style="font-size:11px; font-weight:800; color:var(--primary-light);" id="langTxt">AR</span></button>
      <button class="icon-btn" id="leaderBtn"><svg class="ic"><use href="#i-trophy"/></svg></button>
      <button class="icon-btn" id="profileBtn"><svg class="ic"><use href="#i-user"/></svg></button>
      <button class="icon-btn hidden" id="leaveBtn"><svg class="ic"><use href="#i-logout"/></svg></button>
    </div>
  </header>

  <div class="status-pill offline" id="connPill" style="align-self: center; margin-bottom: 10px;">
    <span class="status-dot"></span><span id="connTxt" data-i18n="connecting">جاري الاتصال...</span>
  </div>

  <div id="toast" class="toast-msg"></div>

  <section id="bootView" style="text-align: center; padding: 70px 0;">
    <div class="spinner"></div><p style="color: var(--text-muted); font-weight: 700;" data-i18n="connecting_server">جاري الاتصال بالخادم الآمن...</p>
  </section>

  <section id="homeView" class="hidden">
    <div class="card" style="text-align: center; padding: 22px 16px;">
      <h2 style="font-size: 20px; font-weight: 900; margin-bottom: 6px;" data-i18n="hero_title">تحدي التخمين والمندس</h2>
      <p style="font-size: 13.5px; color: var(--text-muted); margin-bottom: 18px;" data-i18n="hero_desc">أنشئ غرفة خاصة أو انضم للعب السريع مع لاعبين أونلاين!</p>
      <div class="row" style="margin-bottom: 10px;">
        <button class="btn" id="quickBtn" style="background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);">
          <svg class="ic"><use href="#i-zap"/></svg><span data-i18n="btn_quick">لعب سريع عشوائي</span>
        </button>
      </div>
      <div class="row">
        <button class="btn" id="createBtn">
          <svg class="ic"><use href="#i-plus"/></svg><span data-i18n="btn_create">إنشاء غرفة جديدة</span>
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-title"><svg class="ic"><use href="#i-target"/></svg><span data-i18n="title_join">الانضمام إلى غرفة</span></div>
      <div class="row">
        <input id="joinCodeIn" class="field code-field" maxlength="5" placeholder="ABCDE">
        <button class="btn btn-sm" id="joinBtn"><span data-i18n="btn_join">انضمام</span></button>
      </div>
    </div>
  </section>

  <section id="lobbyView" class="hidden">
    <div class="card" style="text-align: center;">
      <div style="font-size: 12px; color: var(--text-muted); font-weight: 700;" data-i18n="room_code_label">رمز الغرفة الرسمي</div>
      <div class="room-code" id="displayCode">-----</div>
      <div class="row" style="max-width: 270px; margin: 0 auto;">
        <button class="btn btn-secondary btn-sm" id="copyBtn"><svg class="ic"><use href="#i-copy"/></svg><span data-i18n="btn_copy">نسخ</span></button>
        <button class="btn btn-secondary btn-sm" id="shareBtn"><svg class="ic"><use href="#i-share"/></svg><span data-i18n="btn_share">دعوة</span></button>
      </div>
    </div>

    <div class="card">
      <div class="card-title">
        <svg class="ic"><use href="#i-user"/></svg><span data-i18n="players_list">اللاعبون</span>
        <span class="grow"></span><span id="playerCount">0 / 12</span>
      </div>
      <div class="players-grid" id="playersList"></div>
    </div>

    <div class="card">
      <div class="card-title"><span data-i18n="match_settings">إعدادات المباراة</span></div>
      <div style="margin-bottom: 10px;">
        <label style="font-size: 12px; color: var(--text-muted); font-weight: 700;" data-i18n="lbl_mode">نمط اللعبة</label>
        <select id="selMode" class="field">
          <option value="classic">كلاسيكي (مخمن وبقية اللاعبين تلميحات)</option>
          <option value="undercover">المندس / الجاسوس (الكل يعرف الكلمة ما عدا الجاسوس)</option>
          <option value="taboo">الكلمات الممنوعة (تلميح دون ذكر 3 كلمات محظورة)</option>
        </select>
      </div>
      <div style="margin-bottom: 10px;">
        <label style="font-size: 12px; color: var(--text-muted); font-weight: 700;" data-i18n="lbl_category">فئة الكلمات</label>
        <select id="selCat" class="field"></select>
      </div>
      <div class="row">
        <div><label style="font-size: 12px; color: var(--text-muted); font-weight: 700;" data-i18n="lbl_rounds">الجولات</label><select id="selRounds" class="field"></select></div>
        <div><label style="font-size: 12px; color: var(--text-muted); font-weight: 700;" data-i18n="lbl_timer">وقت الجولة</label><select id="selTimer" class="field"></select></div>
      </div>
    </div>

    <p id="lobbyHint" style="font-size: 12px; text-align: center; margin-bottom: 12px; color: var(--text-muted); font-weight: 700;"></p>
    <button class="btn" id="startBtn"><svg class="ic"><use href="#i-play"/></svg><span data-i18n="btn_start">بدء المباراة</span></button>
  </section>

  <section id="gameView" class="hidden">
    <div class="card" style="text-align: center;">
      <div style="font-size: 12px; font-weight: 800; color: var(--primary-light); margin-bottom: 6px;" id="gameModeBanner">نمط كلاسيكي</div>
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
      
      <div id="tabooBox" class="hidden" style="margin-top: 6px;">
        <div style="font-size: 11px; color: var(--danger); font-weight: 800; margin-bottom: 4px;">الكلمات الممنوعة في التلميح:</div>
        <div id="tabooWordsList"></div>
      </div>

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

    <!-- أزرار تفاعلية نقية باستخدام SVG بدلاً من الإيموجيز -->
    <div class="reactions-bar">
      <button class="react-btn" onclick="sendReaction('i-thumbs-up')"><svg class="ic"><use href="#i-thumbs-up"/></svg></button>
      <button class="react-btn" onclick="sendReaction('i-flame')"><svg class="ic" style="color:var(--danger);"><use href="#i-flame"/></svg></button>
      <button class="react-btn" onclick="sendReaction('i-smile')"><svg class="ic" style="color:var(--gold);"><use href="#i-smile"/></svg></button>
      <button class="react-btn" onclick="sendReaction('i-help')"><svg class="ic"><use href="#i-help"/></svg></button>
      <button class="react-btn" onclick="sendReaction('i-zap')"><svg class="ic" style="color:var(--primary-light);"><use href="#i-zap"/></svg></button>
    </div>
  </section>

  <section id="endView" class="hidden">
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

  <div class="modal-overlay hidden" id="leaderModal">
    <div class="modal-box">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
        <h3 style="display: flex; align-items: center; gap: 8px;"><svg class="ic" style="color: var(--gold);"><use href="#i-trophy"/></svg><span data-i18n="top_players">لوحة الصدارة العالمية</span></h3>
        <button class="icon-btn" id="closeLeaderBtn"><svg class="ic"><use href="#i-close"/></svg></button>
      </div>
      <div id="globalLeaderList"></div>
    </div>
  </div>

  <div class="modal-overlay hidden" id="profileModal">
    <div class="modal-box">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
        <h3 style="display: flex; align-items: center; gap: 8px;"><svg class="ic" style="color: var(--primary-light);"><use href="#i-user"/></svg><span data-i18n="profile_title">الملف الشخصي</span></h3>
        <button class="icon-btn" id="closeProfileBtn"><svg class="ic"><use href="#i-close"/></svg></button>
      </div>
      <div style="text-align: center; padding: 6px 0 12px;">
        <div class="avatar-box" id="profAvatarBox" style="width: 64px; height: 64px; margin: 0 auto 10px; font-size: 24px;"></div>
        <h4 style="font-size: 17px; font-weight: 800;" id="profName">لاعب</h4>
        <div class="badge-pill" id="profTitle" style="margin-top: 4px;">مبتدئ</div>
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
    hero_title: "تحدي التخمين والمندس",
    hero_desc: "أنشئ غرفة خاصة أو انضم للعب السريع مع لاعبين أونلاين!",
    btn_quick: "لعب سريع عشوائي",
    btn_create: "إنشاء غرفة جديدة",
    title_join: "الانضمام إلى غرفة",
    btn_join: "انضمام",
    room_code_label: "رمز الغرفة الرسمي",
    btn_copy: "نسخ",
    btn_share: "دعوة",
    players_list: "اللاعبون",
    match_settings: "إعدادات المباراة",
    lbl_mode: "نمط اللعبة",
    lbl_category: "فئة الكلمات",
    lbl_rounds: "الجولات",
    lbl_timer: "وقت الجولة",
    btn_start: "بدء المباراة",
    give_clue_title: "اكتب تلميحاً ذكياً لمساعدة المخمن",
    make_guess_title: "اكتب إجابتك لتخمين الكلمة",
    btn_guess: "تخمين",
    clues_box: "التلميحات",
    guesses_box: "المحاولات",
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
    hero_title: "Social Guessing & Impostor",
    hero_desc: "Create a private room or quick match with online players!",
    btn_quick: "Quick Match",
    btn_create: "Create New Room",
    title_join: "Join a Room",
    btn_join: "Join",
    room_code_label: "Official Room Code",
    btn_copy: "Copy",
    btn_share: "Invite",
    players_list: "Players",
    match_settings: "Match Settings",
    lbl_mode: "Game Mode",
    lbl_category: "Word Category",
    lbl_rounds: "Rounds",
    lbl_timer: "Round Timer",
    btn_start: "Start Match",
    give_clue_title: "Write a clever clue for the guesser",
    make_guess_title: "Guess the target word",
    btn_guess: "Guess",
    clues_box: "Clues",
    guesses_box: "Attempts",
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
    hero_title: "Défi de devinette & imposteur",
    hero_desc: "Créez un salon privé ou rejoignez une partie rapide !",
    btn_quick: "Partie rapide",
    btn_create: "Créer un salon",
    title_join: "Rejoindre un salon",
    btn_join: "Rejoindre",
    room_code_label: "Code du salon",
    btn_copy: "Copier",
    btn_share: "Inviter",
    players_list: "Joueurs",
    match_settings: "Paramètres de la partie",
    lbl_mode: "Mode de jeu",
    lbl_category: "Catégorie",
    lbl_rounds: "Manches",
    lbl_timer: "Temps",
    btn_start: "Lancer la partie",
    give_clue_title: "Écrivez un indice malin",
    make_guess_title: "Devinez le mot secret",
    btn_guess: "Valider",
    clues_box: "Indices",
    guesses_box: "Tentatives",
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
  ar: { celebs: 'مشاهير وثقافة', football: 'كرة قدم وأندية', anime: 'شخصيات أنمي', food: 'أكلات ومأكولات', games: 'ألعاب فيديو', general: 'معلومات عامة' },
  en: { celebs: 'Celebrities & Culture', football: 'Football & Clubs', anime: 'Anime Characters', food: 'Food & Dishes', games: 'Video Games', general: 'General Knowledge' },
  fr: { celebs: 'Célébrités & Culture', football: 'Football & Clubs', anime: "Personnages d'Anime", food: 'Gastronomie', games: 'Jeux Vidéo', general: 'Culture Générale' }
};

let currentLang = localStorage.getItem('game_lang') || 'ar';
let soundEnabled = localStorage.getItem('sound_enabled') !== 'false';

let audioCtx = null;
function getAudioContext() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) audioCtx = new AudioContext();
  }
  if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
  return audioCtx;
}

function playTone(freq, type, duration, gainVal = 0.08) {
  if (!soundEnabled) return;
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    gain.gain.setValueAtTime(gainVal, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch (_) {}
}

const sfx = {
  click: () => playTone(520, 'sine', 0.06, 0.05),
  tick: () => playTone(880, 'triangle', 0.04, 0.04),
  success: () => {
    playTone(523.25, 'sine', 0.12, 0.08);
    setTimeout(() => playTone(659.25, 'sine', 0.12, 0.08), 80);
    setTimeout(() => playTone(783.99, 'sine', 0.22, 0.08), 160);
  },
  timeout: () => {
    playTone(220, 'sawtooth', 0.25, 0.06);
    setTimeout(() => playTone(180, 'sawtooth', 0.35, 0.06), 150);
  }
};

function toggleSound() {
  soundEnabled = !soundEnabled;
  localStorage.setItem('sound_enabled', soundEnabled);
  $('soundBtn').innerHTML = `<svg class="ic"><use href="#i-${soundEnabled ? 'sound' : 'mute'}"/></svg>`;
  toast(soundEnabled ? 'تم تفعيل الصوت' : 'تم كتم الصوت');
}

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
let currentRoomCode = tg?.initDataUnsafe?.start_param?.toUpperCase() || new URLSearchParams(location.search).get('tgWebAppStartParam')?.toUpperCase() || new URLSearchParams(location.search).get('room')?.toUpperCase() || null;
let lastTickedSec = -1;

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

function getTitleByScore(pts) {
  if (pts > 500) return 'أسطورة شكون أنا';
  if (pts > 200) return 'ثعلب التخمين';
  if (pts > 50) return 'محقق ذكي';
  return 'مبتدئ';
}

function renderAvatar(photoUrl, name, id) {
  if (photoUrl) {
    return `<img src="${photoUrl}" class="avatar-img" alt="${name}" onerror="this.remove();">`;
  }
  const color = `hsl(${Math.abs(id * 53)%360},65%,45%)`;
  return `<div style="background:${color}; width:100%; height:100%; display:grid; place-items:center;">${(name||'ل')[0]}</div>`;
}

function updateProfileUI(u) {
  if (!u) return;
  $('profName').textContent = u.name;
  $('profAvatarBox').innerHTML = renderAvatar(u.photo_url, u.name, u.id);
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
      } else if (m.type === 'reaction') {
        spawnReaction(m.icon);
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
    $('connTxt').textContent = (currentLang === 'ar') ? 'غير متصل' : 'Offline';
    setTimeout(connectServer, 2000);
  };
}

setTimeout(() => {
  if (!me) {
    const tgUser = tg?.initDataUnsafe?.user;
    me = tgUser || { id: Math.floor(100000 + Math.random()*900000), first_name: "لاعب" };
    me.name = me.first_name || me.name || "لاعب";
    me.photo_url = tgUser?.photo_url || null;
    updateProfileUI(me);
    switchView('homeView');
  }
}, 3000);

function sendReaction(icon) {
  sendMsg({ type: 'reaction', icon });
  spawnReaction(icon);
}

function spawnReaction(icon) {
  const el = document.createElement('div');
  el.className = 'flying-reaction';
  el.innerHTML = `<svg class="ic"><use href="#${icon}"/></svg>`;
  el.style.left = `${25 + Math.random() * 50}%`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 1800);
}

function launchConfetti() {
  const canvas = $('confettiCanvas');
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  const pieces = Array.from({length: 70}, () => ({
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
  const t = I18N[currentLang];

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
      d.innerHTML = `
        <div class="avatar-box">${renderAvatar(p.photo_url, p.name, p.id)}</div>
        <div class="player-info">
          <div class="player-name">${p.name}${p.id===me.id?' (' + youTxt + ')':''}</div>
          <div class="player-role">${isRoomHost?'<svg class="ic"><use href="#i-crown"/></svg> ' + t.host : (p.online?'Online':'Offline')}</div>
        </div>
      `;
      list.appendChild(d);
    });
  } else if (state.status === 'playing') {
    switchView('gameView');
    const r = state.round;
    const mode = state.settings.mode || 'classic';
    const isGuesser = r.guesser === me.id;
    const isImpostor = r.impostor === me.id;

    if (mode === 'undercover') {
      $('gameModeBanner').textContent = 'نمط المندس / الجاسوس';
      $('roleText').textContent = isImpostor ? 'أنت هو المندس! لا تدعهم يكتشفونك!' : 'اكتب تلميحك واكتشف المندس بينكم';
      $('targetWord').textContent = isImpostor ? '[أنت المندس]' : r.word;
    } else if (mode === 'taboo') {
      $('gameModeBanner').textContent = 'نمط الكلمات الممنوعة (Taboo)';
      $('roleText').textContent = isGuesser ? t.your_turn : `${t.current_guesser} ${getPlayerName(r.guesser)}`;
      $('targetWord').textContent = r.word || 'ـ ـ ـ ـ ـ ـ';
    } else {
      $('gameModeBanner').textContent = 'النمط الكلاسيكي';
      $('roleText').textContent = isGuesser ? t.your_turn : `${t.current_guesser} ${getPlayerName(r.guesser)}`;
      $('targetWord').textContent = r.word || 'ـ ـ ـ ـ ـ ـ';
    }
    $('targetWord').classList.toggle('masked', !r.word && mode !== 'undercover');

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
      banner.className = `result-banner ${r.solved ? 'success' : 'timeout'}`;
      banner.innerHTML = `<svg class="ic"><use href="#i-${r.solved ? 'target' : 'close'}"/></svg><span>${r.solved ? t.guessed_correctly : t.time_up}</span>`;
      if (r.solved) {
        launchConfetti();
        sfx.success();
      } else {
        sfx.timeout();
      }
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

    clearInterval(timerInterval);
    const end = Date.now() + r.left;
    const totalMs = state.settings.timer * 1000;
    const updateTimer = () => {
      const rem = r.active ? Math.max(0, end - Date.now()) : 0;
      const secs = Math.ceil(rem / 1000);
      $('timerSecs').textContent = secs;
      $('timerProgress').style.strokeDashoffset = CIRCUMFERENCE * (1 - rem / totalMs);
      if (r.active && secs <= 5 && secs > 0 && secs !== lastTickedSec) {
        lastTickedSec = secs;
        sfx.tick();
      }
    };
    updateTimer();
    if (r.active) timerInterval = setInterval(updateTimer, 250);
  } else if (state.status === 'ended') {
    switchView('endView');
    clearInterval(timerInterval);
    launchConfetti();
    sfx.success();
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
      col.innerHTML = `
        <div class="podium-avatar">${renderAvatar(p.photo_url, p.name, p.id)}</div>
        <div class="podium-bar">
          <div style="font-weight: 700; font-size: 11px;">${p.name}</div>
          <div style="font-weight: 800; color: var(--gold);">${p.score} ${t.pts}</div>
        </div>
      `;
      podiumBox.appendChild(col);
    });

    const fBox = $('finalScores'); fBox.replaceChildren();
    sorted.forEach((p, idx) => {
      const row = document.createElement('div');
      row.className = 'leader-row';
      row.innerHTML = `
        <span class="rank-pill">${idx+1}</span>
        <div class="avatar-box" style="width:28px; height:28px; margin:0 4px;">${renderAvatar(p.photo_url, p.name, p.id)}</div>
        <span style="flex:1; font-weight:700;">${p.name}</span>
        <b style="color:var(--gold);">${p.score} ${t.pts}</b>
      `;
      fBox.appendChild(row);
    });
    $('restartBtn').classList.toggle('hidden', state.host !== me.id);
  }
}

function renderLeaderboard(list) {
  const box = $('globalLeaderList');
  box.replaceChildren();
  if (!list.length) {
    box.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:20px;">لا توجد سجلات بعد</p>';
    return;
  }
  list.forEach(p => {
    const row = document.createElement('div');
    row.className = 'leader-row';
    row.innerHTML = `
      <span class="rank-pill">${p.rank}</span>
      <span style="flex:1; font-weight:700;">${p.name}</span>
      <span style="font-size:12px; color:var(--text-muted); margin-inline-end:8px;">فوز: ${p.wins}</span>
      <b style="color:var(--gold);">${p.score} ${I18N[currentLang].pts}</b>
    `;
    box.appendChild(row);
  });
}

function leave() {
  sendMsg({ type: 'leave' });
  state = null; currentRoomCode = null; clearInterval(timerInterval);
  switchView('homeView');
}

$('soundBtn').onclick = toggleSound;
$('langBtn').onclick = () => {
  const langs = ['ar', 'en', 'fr'];
  const next = langs[(langs.indexOf(currentLang) + 1) % langs.length];
  setLanguage(next);
};

$('createBtn').onclick = () => { sfx.click(); sendMsg({ type: 'create' }); };
$('quickBtn').onclick = () => { sfx.click(); sendMsg({ type: 'quick_match' }); };
$('joinBtn').onclick = () => {
  sfx.click();
  const code = $('joinCodeIn').value.trim().toUpperCase();
  if (code.length === 5) sendMsg({ type: 'join', code });
};

$('copyBtn').onclick = () => {
  sfx.click();
  if (state?.code) { navigator.clipboard?.writeText(state.code); toast(I18N[currentLang].copied); }
};
$('shareBtn').onclick = () => {
  sfx.click();
  if (!state?.code) return;
  const shareText = `العب معي «شكون أنا؟» في تيليجرام!\nرمز الغرفة: ${state.code}`;
  const url = `https://t.me/share/url?url=${encodeURIComponent('https://t.me/' + 'chkonanabot' + '?startapp=' + state.code)}&text=${encodeURIComponent(shareText)}`;
  if (tg?.openTelegramLink) tg.openTelegramLink(url);
  else window.open(url, '_blank');
};

$('startBtn').onclick = () => { sfx.click(); sendMsg({ type: 'start' }); };
$('restartBtn').onclick = () => { sfx.click(); sendMsg({ type: 'restart' }); };
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
  if (val) { sfx.click(); sendMsg({ type: 'clue', text: val }); $('clueInput').value = ''; }
};
$('sendGuessBtn').onclick = () => {
  const val = $('guessInput').value.trim();
  if (val) { sfx.click(); sendMsg({ type: 'guess', text: val }); $('guessInput').value = ''; }
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
                "photo_url": user.get("photo_url")
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
                    "photo_url": self.players[p].get("photo_url"),
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

    async def join(self, uid, name, ws, photo_url=None):
        if uid not in self.players:
            self.order.append(uid)
            self.players[uid] = {"name": name, "score": 0, "photo_url": photo_url}
        else:
            self.players[uid]["name"] = name
            if photo_url:
                self.players[uid]["photo_url"] = photo_url
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
    photo_url = None
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
                icon = data.get("icon", "i-flame")
                if room:
                    for p_ws in room.conns.values():
                        if p_ws is not ws:
                            await send(p_ws, {"type": "reaction", "icon": icon})
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
                            "name": str(tg_user.get("first_name", "لاعب")).strip()[:20] or "لاعب",
                            "photo_url": tg_user.get("photo_url")
                        }
                    elif "user=" in raw_init:
                        try:
                            for part in raw_init.split("&"):
                                if part.startswith("user="):
                                    u = json.loads(unquote(part[5:]))
                                    user = {
                                        "id": int(u["id"]),
                                        "name": str(u.get("first_name", "لاعب")).strip()[:20] or "لاعب",
                                        "photo_url": u.get("photo_url")
                                    }
                                    break
                        except Exception:
                            pass
                if not user:
                    rnd_id = random.randint(100000, 999999)
                    user = {"id": rnd_id, "name": f"لاعب {str(rnd_id)[-3:]}", "photo_url": None}

                uid = user["id"]
                name = user["name"]
                photo_url = user.get("photo_url")

                if str(uid) in BANNED_USERS:
                    await send(ws, err("تم حظرك من اللعبة من قبل الإدارة."))
                    await ws.close()
                    return ws

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
                await room.join(uid, name, ws, photo_url=photo_url)

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
                await room.join(uid, name, ws, photo_url=photo_url)

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

async def send_tg_msg(session, chat_id, text, reply_markup=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        async with session.post(url, json=payload) as resp:
            if resp.status != 200 and reply_markup:
                payload.pop("reply_markup", None)
                await session.post(url, json=payload)
    except Exception as e:
        print(f"send_tg_msg Exception: {e}")

def extract_cmd(text: str):
    clean = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', text).strip()
    parts = clean.split()
    cmd = None
    cmd_idx = -1
    for i, p in enumerate(parts):
        if p.startswith("/"):
            cmd = p.split("@")[0].lower()
            cmd_idx = i
            break
    args = parts[cmd_idx+1:] if cmd_idx != -1 else []
    return cmd, args, clean

async def handle_tg_message(session, msg):
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    chat_type = chat.get("type", "private")
    user = msg.get("from") or {}
    user_id = user.get("id") or chat_id
    username = (user.get("username") or "").lower()
    raw_text = (msg.get("text") or "").strip()
    if not chat_id or not raw_text:
        return

    if user_id and int(user_id) > 0:
        USERS.add(int(user_id))
        save_db(USERS_FILE, {str(u): True for u in USERS})

    is_owner = (int(user_id) == OWNER_ID) or (username == OWNER_USERNAME.lower())

    clean_cmd, args, clean_text = extract_cmd(raw_text)
    if not clean_cmd:
        return

    # فتح اللعبة في المجموعات داخل تيليجرام كميني أب فقط بدون متصفح خارجي
    if chat_type in ("group", "supergroup"):
        if clean_cmd in ("/start", "/play", "/game"):
            code = GROUP_ROOMS.get(chat_id)
            if not code or code not in ROOMS or ROOMS[code].status == "ended":
                code = new_code()
                ROOMS[code] = Room(code, user_id)
                GROUP_ROOMS[chat_id] = code

            # رابط مباشر يفتح اللعبة داخل نافذة الميني أب في تيليجرام مباشرة
            group_mini_app_url = f"https://t.me/{BOT_USERNAME}?startapp={code}"
            group_kb = {
                "inline_keyboard": [
                    [{"text": "دخول اللعبة في المجموعة", "url": group_mini_app_url}]
                ]
            }
            msg_body = (
                f"<b>تم فتح غرفة اللعب لمجموعتكم!</b>\n"
                f"رمز الغرفة: <code>{code}</code>\n\n"
                f"اضغطوا على الزر بالأسفل لفتح اللعبة كميني أب واللعب معاً:"
            )
            await send_tg_msg(session, chat_id, msg_body, reply_markup=group_kb)
            return

    # المحادثة الخاصة وأوامر المالك
    if chat_type == "private":
        if clean_cmd == "/admin" and is_owner:
            help_txt = (
                f"<b>لوحة تحكم المالك (@{OWNER_USERNAME}):</b>\n\n"
                "<b>/stats</b> : إحصائيات المنصة واللاعبين\n"
                "<b>/broadcast [نص]</b> : إذاعة لجميع المستخدمين\n"
                "<b>/ban [ID]</b> : حظر لاعب من الدخول\n"
                "<b>/unban [ID]</b> : إلغاء حظر لاعب\n"
                "<b>/banned</b> : قائمة المحظورين\n"
                "<b>/reset_scores</b> : تصفير لوحة الصدارة\n"
                "<b>/add_word [فئة] [كلمة] [ممنوعات]</b> : إضافة كلمة\n"
                "<b>/categories</b> : استعراض الفئات وبنك الكلمات\n"
            )
            await send_tg_msg(session, chat_id, help_txt)
            return

        elif clean_cmd == "/stats" and is_owner:
            total_words = sum(len(items) for items in WORDS_DATA.values())
            await send_tg_msg(
                session,
                chat_id,
                f"<b>إحصائيات المنصة المباشرة:</b>\n\n"
                f"إجمالي المستخدمين: <b>{len(USERS)}</b>\n"
                f"المسجلون بالليدربورد: <b>{len(STATS)}</b>\n"
                f"الغرف النشطة الآن: <b>{len(ROOMS)}</b>\n"
                f"بنك الكلمات الكلي: <b>{total_words} كلمة</b>\n"
                f"اللاعبون المحظورون: <b>{len(BANNED_USERS)}</b>"
            )
            return

        elif clean_cmd == "/broadcast" and is_owner:
            m = re.search(r'/broadcast\s+(.+)', clean_text, re.DOTALL | re.IGNORECASE)
            if m:
                bc_text = m.group(1).strip()
                sent = 0
                for uid in list(USERS):
                    if int(uid) > 0:
                        try:
                            await send_tg_msg(session, uid, bc_text)
                            sent += 1
                            await asyncio.sleep(0.04)
                        except Exception:
                            pass
                await send_tg_msg(session, chat_id, f"تم إرسال الإذاعة بنجاح إلى <b>{sent}</b> مستخدماً.")
            else:
                await send_tg_msg(session, chat_id, "طريقة الاستخدام: <code>/broadcast نص الرسالة</code>")
            return

        elif clean_cmd == "/ban" and is_owner:
            if args and args[0].isdigit():
                target_id = args[0]
                BANNED_USERS.add(target_id)
                save_db(BANNED_FILE, {u: True for u in BANNED_USERS})
                for r in ROOMS.values():
                    if int(target_id) in r.conns:
                        try:
                            await r.conns[int(target_id)].close()
                        except Exception:
                            pass
                await send_tg_msg(session, chat_id, f"تم حظر المستخدم <code>{target_id}</code> بنجاح.")
            else:
                await send_tg_msg(session, chat_id, "طريقة الاستخدام: <code>/ban 123456789</code>")
            return

        elif clean_cmd == "/unban" and is_owner:
            if args and args[0].isdigit():
                target_id = args[0]
                if target_id in BANNED_USERS:
                    BANNED_USERS.remove(target_id)
                    save_db(BANNED_FILE, {u: True for u in BANNED_USERS})
                    await send_tg_msg(session, chat_id, f"تم إلغاء حظر المستخدم <code>{target_id}</code> بنجاح.")
                else:
                    await send_tg_msg(session, chat_id, "هذا المستخدم غير موجود في قائمة الحظر.")
            else:
                await send_tg_msg(session, chat_id, "طريقة الاستخدام: <code>/unban 123456789</code>")
            return

        elif clean_cmd == "/banned" and is_owner:
            if not BANNED_USERS:
                await send_tg_msg(session, chat_id, "لا يوجد أي مستخدم محظور حالياً.")
            else:
                b_list = "\n".join(f"• <code>{u}</code>" for u in BANNED_USERS)
                await send_tg_msg(session, chat_id, f"<b>قائمة المحظورين ({len(BANNED_USERS)}):</b>\n{b_list}")
            return

        elif clean_cmd == "/reset_scores" and is_owner:
            STATS.clear()
            save_db(STATS_FILE, STATS)
            await send_tg_msg(session, chat_id, "تم تصفير لوحة الصدارة بنجاح!")
            return

        elif clean_cmd == "/add_word" and is_owner:
            if len(args) >= 2:
                cat = args[0].lower()
                word = args[1].replace("_", " ")
                taboo = [t.strip() for t in args[2].split(",")] if len(args) > 2 else []
                if cat not in WORDS_DATA:
                    cats_str = ", ".join(WORDS_DATA.keys())
                    await send_tg_msg(session, chat_id, f"الفئة غير صحيحة. الفئات المتاحة: <code>{cats_str}</code>")
                    return
                item = {"word": word, "taboo": taboo}
                WORDS_DATA[cat].append(item)
                c_db = load_db(CUSTOM_WORDS_FILE)
                if cat not in c_db:
                    c_db[cat] = []
                c_db[cat].append(item)
                save_db(CUSTOM_WORDS_FILE, c_db)
                taboo_str = ", ".join(taboo) if taboo else "لا توجد"
                await send_tg_msg(
                    session,
                    chat_id,
                    f"<b>تمت إضافة الكلمة بنجاح!</b>\n"
                    f"• الفئة: <code>{cat}</code>\n"
                    f"• الكلمة: <b>{word}</b>\n"
                    f"• الكلمات الممنوعة: <i>{taboo_str}</i>"
                )
            else:
                await send_tg_msg(
                    session,
                    chat_id,
                    "طريقة إضافة كلمة:\n"
                    "<code>/add_word الفئة الكلمة كلمة1,كلمة2,كلمة3</code>\n\n"
                    "مثال:\n"
                    "<code>/add_word football مبابي باريس,ريال,فرنسا</code>"
                )
            return

        elif clean_cmd == "/categories" and is_owner:
            cats_info = [f"• <b>{k}</b>: {len(v)} كلمة" for k, v in WORDS_DATA.items()]
            await send_tg_msg(session, chat_id, "<b>الفئات وبنك الكلمات الحالي:</b>\n" + "\n".join(cats_info))
            return

        if clean_cmd == "/start":
            private_kb = {
                "inline_keyboard": [
                    [{"text": "فتح اللعبة الآن", "web_app": {"url": APP_URL}}],
                    [{"text": "إضافة البوت إلى مجموعة", "url": f"https://t.me/{BOT_USERNAME}?startgroup=true"}]
                ]
            }
            await send_tg_msg(
                session,
                chat_id,
                "مرحباً بك في منصة «شكون أنا؟»\n\n"
                "• اضغط على «فتح اللعبة الآن» لبدء اللعب.\n"
                "• أو أضف البوت إلى مجموعتك وتحد أصدقاءك معاً!",
                reply_markup=private_kb
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
