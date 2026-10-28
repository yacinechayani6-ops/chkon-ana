"""
شكون أنا؟ - ملف بايثون واحد كامل مع نظام توثيق مرن
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
from urllib.parse import parse_qsl, unquote
import aiohttp
from aiohttp import WSMsgType, web

BOT_TOKEN = os.getenv("BOT_TOKEN", "9269122102:AAFxKUbT6Bw4_lIfLWVenBDTWQ1M9_fGzMA")
PORT = int(os.getenv("PORT", "8080"))
ALLOW_GUEST_DEV = True

ROUNDS = (3, 5, 8, 10)
TIMERS = (30, 45, 60, 90)
MAX_PLAYERS = 12

WORDS = {
    "celebs": [
        "الشاب خالد", "الشاب حسني", "ياسمينة خضرا", "زين الدين زيدان", "لخضر بلومي",
        "دحمان الحراشي", "وردة الجزائرية", "بيونة", "عثمان عريوات", "صالح أوقروت",
        "لطفي دوبل كانون", "سولكينغ", "الشاب مامي", "محمد فلاق", "سليمان عازم",
        "مفدي زكريا", "كاتب ياسين", "أحمد رضا حوحو", "عائشة عجوري", "حسان الحساني",
        "الشابة الزهوانية", "الشاب بلال", "إيدير", "بلاوي الهواري", "أحمد وهبي",
        "طاهر جعوط", "مصطفى كاتب", "بوعلام بسايح", "محمد ديب", "آسيا جبار"
    ],
    "football": [
        "رياض محرز", "إسماعيل بن ناصر", "يوسف بلايلي", "إسلام سليماني", "بغداد بونجاح",
        "سفيان فيغولي", "رايس مبولحي", "مولودية الجزائر", "شبيبة القبائل", "شباب بلوزداد",
        "اتحاد الجزائر", "وفاق سطيف", "ريال مدريد", "برشلونة", "مانشستر سيتي",
        "ليفربول", "بايرن ميونخ", "باريس سان جيرمان", "ليونيل ميسي", "كريستيانو رونالدو",
        "كيليان مبابي", "إيرلينغ هالاند", "لوكا مودريتش", "كريم بنزيما", "محمد صلاح",
        "أندريه أونانا", "أشرف حكيمي", "ياسين بونو", "كارلو أنشيلوتي", "بيب غوارديولا"
    ],
    "anime": [
        "ناروتو", "لوفي", "غوكو", "ساسكي", "رورونوا زورو", "ليفاي أكرمان",
        "إيرين ييغر", "كونان إيدوجاوا", "فيجيتا", "إيتاشي أوتشيها", "لايت ياغامي",
        "غون فريكس", "كيلوا زولديك", "تانجيرو كامادو", "ساتورو غوجو", "سايتاما",
        "إدوارد إلريك", "كاكاشي هاتاكي", "ميكاسا أكرمان", "شانكس", "مادارا أوتشيها",
        "كوروما", "هيسوكا", "إيتادوري يوجي", "كانيكي كين", "ريوك", "ترانكس"
    ],
    "games": [
        "ماينكرافت", "فورتنايت", "فيفا", "ببجي", "غراند ثفت أوتو",
        "ليغ أوف ليجيندز", "فالورانت", "كول أوف ديوتي", "فري فاير", "روبلوكس",
        "أمونغ آس", "كلاش أوف كلانس", "غود أوف وار", "ريد ديد ريدمبشن", "ذا ويتشر",
        "إلدن رينغ", "أساسنز كريد", "كاونتر سترايك", "أوفرواتش", "سوبر ماريو",
        "بوكيمون", "تيكن", "مورتال كومبات", "ريزدنت إيفل", "تومب رايدر"
    ],
    "movies": [
        "تيتانيك", "الأسد الملك", "بريكينغ باد", "قيامة أرطغرل", "صراع العروش",
        "إنترستيلار", "العراب", "هاري بوتر", "بريزون بريك", "بيكي بلايندرز",
        "إنسيبشن", "أفاتار", "غلاديايتر", "الجوكر", "ماتريكس",
        "باتمان", "سبايدرمان", "سيد الخواتم", "فايكنغز", "تشيرنوبيل",
        "كازابلانكا", "فارس الظلام", "لعبة الحبار", "المنتقمون", "شيرلوك هولمز"
    ],
    "animals": [
        "الفيل", "الزرافة", "البطريق", "القط", "الأسد",
        "النسر", "الدلفين", "الذئب", "الكنغر", "الباندا",
        "الحرباء", "البومة", "النمر", "الدب القطبي", "الثعلب",
        "الصقر", "الحوت الأزرق", "الأخطبوط", "الكوالا", "القرد",
        "التمساح", "الفهد", "السلحفاة", "القندس", "الراكون"
    ],
    "food": [
        "الشخشوخة", "الكسكسي", "الشربة فريك", "المحجوبة", "الرشتة",
        "طاجين الزيتون", "البوراك", "الكرنتيكا", "المسمن", "البقلاوة",
        "المقروط", "الزلابية", "الشكشوكة", "الطمينة", "قلب اللوز",
        "البغرير", "الدويدة", "العصبان", "التليتلي", "البركوكس",
        "المطلوع", "الكسرة", "الدوبارة", "الحميس", "الشطيطحة"
    ],
    "general": [
        "القمر", "الأوكسجين", "برج إيفل", "الكهرباء", "الأهرامات",
        "الإنترنت", "المقراب الفلكي", "الغواصة", "الطائرة", "البركان",
        "الصحراء الكبرى", "البوصلة", "المجهر الإلكتروني", "المجموعة الشمسية", "الجاذبية",
        "نهر النيل", "سور الصين العظيم", "المحيط الهادئ", "الطباعة", "الذكاء الاصطناعي",
        "القنبلة الذرية", "الاحتباس الحراري", "الأقمار الصناعية", "الرادار", "ساعة بيغ بن"
    ],
}

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
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #090814;
  --bg-subtle: #0f0c22;
  --surface: #14112c;
  --surface-hover: #1c183d;
  --surface-active: #231e4a;
  --border: rgba(168, 85, 247, 0.16);
  --border-focus: rgba(168, 85, 247, 0.45);
  --text: #f8f7ff;
  --text-muted: #948fb3;
  --text-dim: #676188;
  --primary: #9333ea;
  --primary-light: #a855f7;
  --gold: #eab308;
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
  font-family: "Cairo", system-ui, sans-serif;
  font-size: 14.5px;
  line-height: 1.5;
  color: var(--text);
  background: radial-gradient(1000px 500px at 50% -120px, rgba(147, 51, 234, 0.22), transparent 75%), var(--bg);
  user-select: none;
}
.app { max-width: 480px; margin: 0 auto; min-height: 100vh; display: flex; flex-direction: column; padding: 16px; }
.top-nav { display: flex; align-items: center; gap: 12px; padding: 8px 0 16px; }
.brand-badge { width: 40px; height: 40px; border-radius: 12px; background: var(--grad-primary); display: grid; place-items: center; font-size: 20px; }
.grow { flex: 1; }
.status-pill { display: inline-flex; align-items: center; gap: 6px; font-size: 11.5px; font-weight: 700; padding: 5px 10px; border-radius: 99px; background: var(--surface); border: 1px solid var(--border); color: var(--text-muted); }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--success); }
.status-pill.offline .status-dot { background: var(--danger); }
.icon-btn { width: 38px; height: 38px; border-radius: 12px; border: 1px solid var(--border); background: var(--surface); color: var(--text); display: grid; place-items: center; cursor: pointer; }
.card { background: var(--grad-surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; margin-bottom: 12px; }
.card-title { font-size: 13.5px; font-weight: 700; color: var(--text-muted); margin-bottom: 12px; }
.field { width: 100%; font-family: inherit; font-size: 14px; color: var(--text); background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 12px 14px; outline: none; }
.field:focus { border-color: var(--border-focus); }
.code-field { text-align: center; letter-spacing: 0.25em; font-family: ui-monospace, Consolas, monospace; font-weight: 800; font-size: 18px; text-transform: uppercase; }
.row { display: flex; gap: 8px; }
.row > * { flex: 1; min-width: 0; }
.btn { width: 100%; display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 0; border-radius: var(--radius-md); padding: 13px 18px; font-family: inherit; font-size: 14.5px; font-weight: 800; color: #fff; background: var(--grad-primary); cursor: pointer; }
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
.btn-secondary { background: var(--surface-hover); border: 1px solid var(--border); color: var(--text); }
.btn-sm { width: auto; flex: none; padding: 12px 18px; }
.room-code { font-family: ui-monospace, Consolas, monospace; font-size: 38px; font-weight: 900; letter-spacing: 0.3em; text-indent: 0.3em; background: var(--grad-primary); -webkit-background-clip: text; background-clip: text; color: transparent; text-align: center; margin: 10px 0; }
.players-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.player-item { display: flex; align-items: center; gap: 10px; padding: 10px; border-radius: var(--radius-md); background: var(--bg-subtle); border: 1px solid var(--border); }
.player-item.offline { opacity: 0.5; }
.avatar-badge { width: 36px; height: 36px; border-radius: 50%; display: grid; place-items: center; font-weight: 800; color: #fff; flex: none; }
.player-name { font-weight: 700; font-size: 13.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.timer-container { position: relative; width: 110px; height: 110px; margin: 0 auto 12px; }
.timer-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.timer-track { fill: none; stroke: var(--bg-subtle); stroke-width: 7; }
.timer-progress { fill: none; stroke: var(--primary-light); stroke-width: 7; stroke-linecap: round; }
.timer-content { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.timer-num { font-size: 32px; font-weight: 900; }
.target-word { min-height: 50px; display: grid; place-items: center; font-size: 28px; font-weight: 900; color: var(--gold); margin: 6px 0; }
.target-word.masked { letter-spacing: 0.15em; color: var(--text-muted); }
.feed-box { display: flex; flex-direction: column; gap: 8px; max-height: 160px; overflow-y: auto; }
.feed-item { background: var(--bg-subtle); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 12px; font-size: 13px; }
.feed-item.correct { border-color: rgba(16, 185, 129, 0.45); color: var(--success); }
.leader-row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }
.rank-pill { width: 24px; height: 24px; border-radius: 50%; background: var(--bg-subtle); display: grid; place-items: center; font-size: 12px; font-weight: 800; }
.toast-msg { position: fixed; inset-inline: 0; bottom: 24px; margin: auto; width: max-content; background: var(--surface-active); border: 1px solid var(--border); padding: 10px 16px; border-radius: var(--radius-md); font-weight: 700; opacity: 0; transform: translateY(12px); transition: 0.2s; pointer-events: none; z-index: 100; }
.toast-msg.show { opacity: 1; transform: translateY(0); }
.hidden { display: none !important; }
.spinner { width: 32px; height: 32px; border-radius: 50%; border: 3px solid var(--border); border-top-color: var(--primary-light); animation: spin 0.8s linear infinite; margin: 0 auto 12px; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>

<div class="app">
  <header class="top-nav">
    <div class="brand-badge">🎯</div>
    <div style="margin-inline-start: 8px;">
      <h1 style="font-size: 17px; font-weight: 800;">شكون أنا؟</h1>
      <p style="font-size: 11px; color: var(--text-muted);">لعبة التخمين الجماعي</p>
    </div>
    <div class="grow"></div>
    <div class="status-pill offline" id="connPill"><span class="status-dot"></span><span id="connTxt">جاري الاتصال</span></div>
    <button class="icon-btn hidden" id="leaveBtn">🚪</button>
  </header>

  <div id="toast" class="toast-msg"></div>

  <section id="bootView" style="text-align: center; padding: 80px 0;">
    <div class="spinner"></div><p style="color: var(--text-muted); font-weight: 700;">جاري الاتصال بالخادم...</p>
  </section>

  <section id="homeView" class="hidden">
    <div class="card" style="text-align: center; padding: 24px 16px;">
      <h2 style="font-size: 20px; font-weight: 900; margin-bottom: 6px;">تحدي التخمين</h2>
      <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 18px;">أنشئ غرفة أو انضم لغرفة أصدقائك عبر الرمز.</p>
      <button class="btn" id="createBtn">إنشاء غرفة جديدة</button>
    </div>
    <div class="card">
      <div class="card-title">الانضمام إلى غرفة</div>
      <div class="row">
        <input id="joinCodeIn" class="field code-field" maxlength="5" placeholder="ABCDE">
        <button class="btn btn-sm" id="joinBtn">انضمام</button>
      </div>
    </div>
  </section>

  <section id="lobbyView" class="hidden">
    <div class="card" style="text-align: center;">
      <div style="font-size: 12px; color: var(--text-muted);">رمز الغرفة</div>
      <div class="room-code" id="displayCode">-----</div>
      <div class="row" style="max-width: 260px; margin: 0 auto;">
        <button class="btn btn-secondary btn-sm" id="copyBtn">نسخ الرمز</button>
        <button class="btn btn-secondary btn-sm" id="shareBtn">مشاركة</button>
      </div>
    </div>
    <div class="card">
      <div class="card-title">اللاعبون المتواجدون (<span id="playerCount">0</span>/12)</div>
      <div class="players-grid" id="playersList"></div>
    </div>
    <div class="card">
      <div class="card-title">إعدادات المباراة</div>
      <div style="margin-bottom: 10px;"><label style="font-size: 12px; color: var(--text-muted);">الفئة</label><select id="selCat" class="field"></select></div>
      <div class="row">
        <div><label style="font-size: 12px; color: var(--text-muted);">الجولات</label><select id="selRounds" class="field"></select></div>
        <div><label style="font-size: 12px; color: var(--text-muted);">الوقت</label><select id="selTimer" class="field"></select></div>
      </div>
    </div>
    <p id="lobbyHint" style="font-size: 12px; text-align: center; margin-bottom: 10px; color: var(--text-muted);"></p>
    <button class="btn" id="startBtn">بدء المباراة</button>
  </section>

  <section id="gameView" class="hidden">
    <div class="card" style="text-align: center;">
      <div class="timer-container">
        <svg class="timer-svg" viewBox="0 0 120 120">
          <circle class="timer-track" cx="60" cy="60" r="52"/>
          <circle id="timerProgress" class="timer-progress" cx="60" cy="60" r="52"/>
        </svg>
        <div class="timer-content"><div class="timer-num" id="timerSecs">0</div></div>
      </div>
      <div style="font-weight: 700; color: var(--text-muted);" id="roleText">...</div>
      <div class="target-word" id="targetWord">...</div>
      <div id="resultBanner" class="hidden" style="font-weight: 700; margin-top: 6px;"></div>
    </div>
    <div class="card hidden" id="clueCard">
      <div class="card-title">اكتب تلميحاً ذكياً للمخمن</div>
      <div class="row"><input id="clueInput" class="field" maxlength="80" placeholder="تلميح بدون ذكر الكلمة"><button class="btn btn-sm" id="sendClueBtn">إرسال</button></div>
    </div>
    <div class="card hidden" id="guessCard">
      <div class="card-title">اكتب الكلمة التي تخمنها</div>
      <div class="row"><input id="guessInput" class="field" maxlength="40" placeholder="ما هي الكلمة؟"><button class="btn btn-sm" id="sendGuessBtn">تخمين</button></div>
    </div>
    <div class="row" style="margin-bottom: 12px;">
      <div class="card" style="margin: 0;"><div class="card-title">التلميحات</div><div class="feed-box" id="cluesFeed"></div></div>
      <div class="card" style="margin: 0;"><div class="card-title">المحاولات</div><div class="feed-box" id="guessesFeed"></div></div>
    </div>
    <div class="card"><div class="card-title">الترتيب المباشر</div><div id="liveScores"></div></div>
  </section>

  <section id="endView" class="hidden">
    <div class="card" style="text-align: center; padding: 24px 16px;">
      <h2 style="font-size: 22px; font-weight: 900;" id="winnerTitle">...</h2>
      <p style="color: var(--text-muted); margin-top: 4px;" id="winnerSub">...</p>
    </div>
    <div class="card"><div class="card-title">النتائج النهائية</div><div id="finalScores"></div></div>
    <div class="row">
      <button class="btn" id="restartBtn">جولة جديدة</button>
      <button class="btn btn-secondary" id="exitHomeBtn">الرئيسية</button>
    </div>
  </section>
</div>

<script>
const tg = window.Telegram?.WebApp;
try { tg?.ready(); tg?.expand(); } catch (_) {}

const CATEGORIES = {
  celebs: 'مشاهير وثقافة',
  football: 'كرة قدم وأندية',
  anime: 'شخصيات أنمي',
  games: 'ألعاب فيديو',
  movies: 'أفلام ومسلسلات',
  animals: 'عالم الحيوان',
  food: 'أكلات ومأكولات',
  general: 'معلومات عامة'
};

const $ = id => document.getElementById(id);
const CIRCUMFERENCE = 2 * Math.PI * 52;
const VIEWS = ['homeView', 'lobbyView', 'gameView', 'endView'];

let ws = null, me = null, state = null, timerInterval = null;
let currentRoomCode = new URLSearchParams(location.search).get('room')?.toUpperCase() || null;

const populateSelect = (el, arr) => {
  el.replaceChildren();
  for (const [val, label] of arr) el.add(new Option(label, val));
};
populateSelect($('selCat'), Object.entries(CATEGORIES));
populateSelect($('selRounds'), [3, 5, 8, 10].map(n => [n, `${n} جولات`]));
populateSelect($('selTimer'), [30, 45, 60, 90].map(n => [n, `${n} ثانية`]));
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
    $('connTxt').textContent = 'متصل';
    // إرسال كائن المستخدم مباشرة إلى السيرفر
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
        if (currentRoomCode) sendMsg({ type: 'join', code: currentRoomCode });
        else switchView('homeView');
      } else if (m.type === 'state') {
        state = m.state;
        currentRoomCode = state.code;
        render();
      } else if (m.type === 'error') {
        toast(m.message);
        if (!state) switchView('homeView');
      }
    } catch (_) {}
  };
  ws.onclose = () => {
    $('connPill').classList.add('offline');
    $('connTxt').textContent = 'غير متصل';
    setTimeout(connectServer, 2000);
  };
}

const getPlayerName = id => state?.players.find(p => p.id === id)?.name || 'لاعب';

function render() {
  if (!state || !me) return switchView('homeView');
  if (state.status === 'lobby') {
    switchView('lobbyView');
    const isHost = state.host === me.id;
    $('displayCode').textContent = state.code;
    $('playerCount').textContent = state.players.length;
    $('selCat').value = state.settings.category;
    $('selRounds').value = state.settings.rounds;
    $('selTimer').value = state.settings.timer;
    ['selCat', 'selRounds', 'selTimer'].forEach(id => { $(id).disabled = !isHost; });
    $('startBtn').disabled = !isHost || state.players.length < 2;

    const list = $('playersList');
    list.replaceChildren();
    state.players.forEach(p => {
      const d = document.createElement('div');
      d.className = `player-item ${p.online ? '' : 'offline'}`;
      d.innerHTML = `<div class="avatar-badge" style="background: hsl(${Math.abs(p.id * 53)%360},65%,45%)">${(p.name||'ل')[0]}</div>
                     <div class="player-name">${p.name}${p.id===me.id?' (أنت)':''} ${p.id===state.host?'👑':''}</div>`;
      list.appendChild(d);
    });
  } else if (state.status === 'playing') {
    switchView('gameView');
    const r = state.round;
    const isGuesser = r.guesser === me.id;
    $('roleText').textContent = isGuesser ? '🎯 دورك للتخمين الآن' : `💡 المخمن الحالي: ${getPlayerName(r.guesser)}`;
    $('targetWord').textContent = r.word || 'ـ ـ ـ ـ ـ ـ';
    $('targetWord').classList.toggle('masked', !r.word);

    $('clueCard').classList.toggle('hidden', isGuesser || !r.active);
    $('guessCard').classList.toggle('hidden', !isGuesser || !r.active);

    const banner = $('resultBanner');
    if (!r.active) {
      banner.classList.remove('hidden');
      banner.textContent = r.solved ? '🎉 تم التخمين بنجاح!' : '⏰ انتهى الوقت!';
      banner.style.color = r.solved ? 'var(--success)' : 'var(--danger)';
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
      item.textContent = g.text + (g.ok ? ' ✅' : '');
      gFeed.appendChild(item);
    });

    const sBox = $('liveScores'); sBox.replaceChildren();
    [...state.players].sort((a,b)=>b.score-a.score).forEach((p, idx) => {
      const row = document.createElement('div');
      row.className = 'leader-row';
      row.innerHTML = `<span class="rank-pill">${idx+1}</span><span style="flex:1;">${p.name}</span><b>${p.score} ن</b>`;
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
    $('winnerTitle').textContent = `الفائز: ${sorted[0]?.name || 'لا أحد'}`;
    $('winnerSub').textContent = `الرصيد: ${sorted[0]?.score || 0} نقطة`;
    const fBox = $('finalScores'); fBox.replaceChildren();
    sorted.forEach((p, idx) => {
      const row = document.createElement('div');
      row.className = 'leader-row';
      row.innerHTML = `<span class="rank-pill">${idx+1}</span><span style="flex:1;">${p.name}</span><b>${p.score} ن</b>`;
      fBox.appendChild(row);
    });
    $('restartBtn').classList.toggle('hidden', state.host !== me.id);
  }
}

function leave() {
  sendMsg({ type: 'leave' });
  state = null; currentRoomCode = null; clearInterval(timerInterval);
  switchView('homeView');
}

$('createBtn').onclick = () => sendMsg({ type: 'create' });
$('joinBtn').onclick = () => {
  const code = $('joinCodeIn').value.trim().toUpperCase();
  if (code.length === 5) sendMsg({ type: 'join', code });
};
$('copyBtn').onclick = () => {
  if (state?.code) { navigator.clipboard?.writeText(state.code); toast('تم نسخ رمز الغرفة'); }
};
$('shareBtn').onclick = () => {
  if (!state?.code) return;
  const url = `https://t.me/share/url?url=${encodeURIComponent(location.origin + '/?room=' + state.code)}&text=${encodeURIComponent('العب معي في شكون أنا؟!')}`;
  window.open(url, '_blank');
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
    """توثيق مرن لبيانات تيليجرام"""
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
                return "فقط مضيف الغرفة يمكنه بدء المباراة"
            if len([p for p in self.order if p in self.conns]) < 2:
                return "يلزم وجود لاعبين متصلين على الأقل للبدء"
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
                return "فقط مضيف الغرفة يمكنه إعادة اللعبة"
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
                return "ليس متاحاً لك تقديم تلميح الآن"
            text = str(data.get("text", "")).strip()[:80]
            if not text:
                return "يرجى كتابة نص التلميح"
            if clue_has_forbidden_word(text, r["word"]):
                return "ممنوع ذكر الكلمة المطلوبة أو جزء منها في التلميح"
            r["clues"].append({"by": uid, "text": text})
            await self.broadcast()
            return None

        if t == "guess":
            if self.status != "playing" or not r or not r["active"] or uid != r["guesser"]:
                return "ليس دورك في التخمين حالياً"
            text = str(data.get("text", "")).strip()[:40]
            n = norm(text)
            if not n:
                return "يرجى كتابة إجابة صالحة"
            if n in r["gn"]:
                return "لقد تمت تجربة هذه الإجابة مسبقاً"
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

            if t == "auth":
                raw_init = str(data.get("initData", ""))
                # 1. محاولة التحقق المشفر
                user = verify_init_data(raw_init)
                
                # 2. إذا تعذر التحقق المشفر، استخراج معلومات اللاعب مباشرة من تيليجرام
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
                
                # 3. معرف عشوائي كحل بديل أخير
                if not user and ALLOW_GUEST_DEV:
                    rnd_id = random.randint(100000, 999999)
                    user = {"id": rnd_id, "name": f"لاعب {str(rnd_id)[-3:]}"}

                uid, name = user["id"], user["name"]
                await send(ws, {"type": "authed", "user": {"id": uid, "name": name}})

            elif uid is None:
                continue

            elif t in ("create", "join"):
                if t == "create":
                    code = new_code()
                    target = ROOMS[code] = Room(code, uid)
                else:
                    target = ROOMS.get(str(data.get("code", "")).upper().strip())
                    if target is None:
                        await send(ws, err("رمز الغرفة غير صحيح أو منتهي"))
                        continue
                    if uid not in target.players and (
                        target.status != "lobby" or len(target.players) >= MAX_PLAYERS
                    ):
                        await send(ws, err("الغرفة ممتلئة أو بدأت المباراة"))
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
                    error = "حدث خطأ أثناء معالجة الطلب"
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


async def send_tg(session, chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        await session.post(url, json={"chat_id": chat_id, "text": text})
    except Exception:
        pass


async def handle_tg_message(session, msg):
    chat_id = msg.get("chat", {}).get("id")
    text = (msg.get("text") or "").strip()
    if not chat_id:
        return

    if text.startswith("/start"):
        await send_tg(
            session,
            chat_id,
            "مرحباً بك في منصة «شكون أنا؟» 🎮\n\n"
            "اضغط على زر اللعبة أسفل الشاشة لبدء اللعب مباشرة ومشاركة الغرفة مع أصدقائك!"
        )
    elif text.startswith("/rules"):
        await send_tg(
            session,
            chat_id,
            "[ قواعد اللعبة ]\n\n"
            "- مخمّن واحد وبقية اللاعبين يكتبون تلميحات مفيدة.\n"
            "- ممنوع ذكر الكلمة المطلوبة في التلميح.\n"
            "- التخمين الصحيح = 10 نقاط للمخمن و 2 نقاط لكل تلميح مساعد."
        )
    elif text.startswith("/help"):
        await send_tg(session, chat_id, "الأوامر المتاحة:\n/start - بدء البوت\n/rules - شرح القواعد\n/help - المساعدة")


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
            await asyncio.sleep(0.5)


async def main():
    app = web.Application()
    app.add_routes([web.get("/", index), web.get("/ws", ws_handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()

    asyncio.create_task(cleanup())
    asyncio.create_task(bot_polling())

    print(f"Server is running on port {PORT}...")
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
