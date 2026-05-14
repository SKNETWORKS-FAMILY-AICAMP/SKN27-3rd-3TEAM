import streamlit as st
import streamlit.components.v1 as components
import os
import sys
import base64
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import inject_common_ui
from game2.styles import inject_game2_styles

st.set_page_config(
    page_title="포켓몬 메모리 게임",
    page_icon="https://pokemonkorea.co.kr/img/_con.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def get_base64_img(file_name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for sub in ("main_background", "main_character", ""):
        path = (
            os.path.join(base_dir, "img", sub, file_name)
            if sub
            else os.path.join(base_dir, "img", file_name)
        )
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""


bg_img = get_base64_img("game1_background.png")
inject_common_ui(spacer=False)
inject_game2_styles(bg_img)

ARTWORK = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"

POKEMON_POOL = [
    (1, "이상해씨"), (4, "파이리"),    (7, "꼬부기"),   (25, "피카츄"),
    (39, "푸린"),    (52, "나옹"),     (54, "고라파덕"), (94, "팬텀"),
    (131, "라프라스"),(133, "이브이"), (143, "잠만보"), (149, "망나뇽"),
    (150, "뮤츠"),   (6, "리자몽"),    (9, "거북왕"),
]

pool_json = json.dumps(
    [{"id": pid, "name": name, "img": f"{ARTWORK}/{pid}.png"} for pid, name in POKEMON_POOL],
    ensure_ascii=False,
)

GAME_HTML = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;font-family:'Noto Sans KR',sans-serif;color:#fff;overflow:hidden}}
#wrap{{max-width:680px;margin:0 auto;padding:12px}}

#title{{text-align:center;margin-bottom:14px}}
#title h1{{font-size:1.7rem;font-weight:900;font-family:Outfit,sans-serif;
  background:linear-gradient(90deg,#FF88FF,#88FFFF);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}}
#title p{{color:#aaa;font-size:.82rem;margin-top:4px}}

#diff-bar{{display:flex;gap:10px;margin-bottom:14px}}
.diff-btn{{flex:1;padding:10px 8px;background:rgba(8,4,22,.88);
  border:2px solid rgba(120,0,200,.45);border-radius:14px;cursor:pointer;
  text-align:center;transition:all .22s;backdrop-filter:blur(16px)}}
.diff-btn:hover{{border-color:rgba(200,0,255,.85);box-shadow:0 0 16px rgba(200,0,255,.28)}}
.diff-btn.active{{border-color:#FF00FF;box-shadow:0 0 24px rgba(255,0,255,.45);
  background:rgba(30,0,60,.92)}}
.diff-label{{font-size:.95rem;font-weight:900;color:#FF88FF;font-family:Outfit,sans-serif}}
.diff-sub{{font-size:.7rem;color:#aaa;margin-top:3px}}

#stats{{display:flex;justify-content:space-around;background:rgba(8,4,22,.88);
  border:1px solid rgba(200,0,255,.38);border-radius:14px;padding:9px;margin-bottom:12px}}
.stat{{text-align:center}}
.slabel{{font-size:.6rem;color:#aaa;text-transform:uppercase;letter-spacing:1px}}
.sval{{font-size:1.2rem;font-weight:900;color:#FF88FF;font-family:monospace}}

:root{{--cs:100px}}
#grid{{display:grid;gap:8px;justify-items:center}}
.card{{width:var(--cs);height:var(--cs);perspective:600px;cursor:pointer}}
.inner{{width:100%;height:100%;position:relative;transform-style:preserve-3d;
  transition:transform .42s cubic-bezier(.4,0,.2,1);border-radius:12px}}
.card.flipped .inner,.card.matched .inner{{transform:rotateY(180deg)}}
.card.matched .front{{border-color:#00FF99!important;box-shadow:0 0 18px #00FF9966}}
.card.shake{{animation:shake .36s}}
@keyframes shake{{0%,100%{{transform:translateX(0)}}25%{{transform:translateX(-6px)}}75%{{transform:translateX(6px)}}}}
.face{{position:absolute;width:100%;height:100%;backface-visibility:hidden;
  border-radius:12px;display:flex;align-items:center;justify-content:center;overflow:hidden}}
.back{{background:linear-gradient(135deg,#2a0060,#1a003a,#0a001a);
  border:2px solid rgba(140,0,255,.65);
  box-shadow:0 4px 14px rgba(0,0,0,.6),inset 0 0 18px rgba(100,0,255,.12)}}
.back::after{{content:'';width:54%;height:54%;
  background:url('https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png') center/contain no-repeat;
  opacity:.85;filter:drop-shadow(0 0 8px rgba(200,0,255,.6))}}
.front{{background:rgba(8,4,22,.95);border:2px solid rgba(200,0,255,.5);
  transform:rotateY(180deg);flex-direction:column;gap:3px}}
.front img{{width:70%;height:70%;object-fit:contain;filter:drop-shadow(0 2px 5px rgba(0,0,0,.8))}}
.pk-name{{font-size:10px;font-weight:700;color:#CC88FF;text-align:center}}

#restart{{display:block;width:100%;padding:10px;margin-top:10px;
  background:linear-gradient(90deg,#FF00FF,#7700EE,#00FFFF);color:#fff;
  border:none;border-radius:50px;font-size:.9rem;font-weight:900;cursor:pointer;
  box-shadow:0 5px 20px rgba(255,0,255,.4);transition:all .22s;letter-spacing:1px}}
#restart:hover{{transform:scale(1.03);box-shadow:0 9px 30px rgba(0,255,255,.5)}}

#victory{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.92);z-index:9999;
  align-items:center;justify-content:center;backdrop-filter:blur(16px);
  -webkit-backdrop-filter:blur(16px)}}
#victory.show{{display:flex}}
#vcard{{background:rgba(8,4,22,.98);border:2px solid rgba(255,215,0,.9);border-radius:28px;
  padding:36px 48px;text-align:center;max-width:380px;width:90%;
  box-shadow:0 0 90px rgba(255,215,0,.28);animation:pop .5s cubic-bezier(.34,1.56,.64,1)}}
@keyframes pop{{from{{transform:scale(.5);opacity:0}}to{{transform:scale(1);opacity:1}}}}
#vcard h2{{font-size:2.2rem;font-weight:900;
  background:linear-gradient(90deg,gold,orange);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;margin-bottom:10px}}
.vstats{{color:#ccc;font-size:.95rem;margin:12px 0 20px;line-height:2.1}}
.vstats span{{color:#FF88FF;font-weight:900}}
#play-again{{padding:11px 34px;background:linear-gradient(90deg,gold,orange);
  color:#000;border:none;border-radius:50px;font-size:.95rem;font-weight:900;
  cursor:pointer;transition:all .22s}}
#play-again:hover{{transform:scale(1.07);box-shadow:0 7px 26px rgba(255,215,0,.5)}}
</style></head>
<body>
<div id="wrap">
  <div id="title">
    <h1>🃏 포켓몬 메모리 게임</h1>
    <p>카드를 뒤집어 같은 포켓몬 짝을 찾아보세요!</p>
  </div>

  <div id="diff-bar">
    <div class="diff-btn" id="d-easy" onclick="setDiff('easy')">
      <div class="diff-label">쉬움</div>
      <div class="diff-sub">3×4 &middot; 6쌍</div>
    </div>
    <div class="diff-btn active" id="d-normal" onclick="setDiff('normal')">
      <div class="diff-label">보통</div>
      <div class="diff-sub">4×4 &middot; 8쌍</div>
    </div>
    <div class="diff-btn" id="d-hard" onclick="setDiff('hard')">
      <div class="diff-label">어려움</div>
      <div class="diff-sub">5×6 &middot; 15쌍</div>
    </div>
  </div>

  <div id="stats">
    <div class="stat"><div class="slabel">⏱ 시간</div><div class="sval" id="timer">00:00</div></div>
    <div class="stat"><div class="slabel">🎯 시도</div><div class="sval" id="moves">0</div></div>
    <div class="stat"><div class="slabel">✅ 맞춤</div><div class="sval" id="matched">0</div></div>
    <div class="stat"><div class="slabel">🃏 남은</div><div class="sval" id="remain">-</div></div>
  </div>

  <div id="grid"></div>
  <button id="restart" onclick="restart()">🔄 다시 시작</button>
</div>

<div id="victory">
  <div id="vcard">
    <h2>🏆 클리어!</h2>
    <div class="vstats">
      소요 시간: <span id="ft">-</span><br>
      총 시도: <span id="fm">-</span><br>
      정확도: <span id="fa">-</span>
    </div>
    <button id="play-again" onclick="restart()">🎮 다시 플레이</button>
  </div>
</div>

<script>
const POOL = {pool_json};
const DIFFS = {{
  easy:   {{cols:3, pairs:6,  cs:110}},
  normal: {{cols:4, pairs:8,  cs:100}},
  hard:   {{cols:5, pairs:15, cs:80}},
}};

let cur='normal', deck=[], flipped=[], matched=0, moves=0, secs=0, ticker=null, lock=false;

function fmt(s){{
  return String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');
}}

function shuffle(a){{
  const b=[...a];
  for(let i=b.length-1;i>0;i--){{
    const j=Math.floor(Math.random()*(i+1));
    [b[i],b[j]]=[b[j],b[i]];
  }}
  return b;
}}

function setDiff(key){{
  cur=key;
  document.querySelectorAll('.diff-btn').forEach(function(el){{el.classList.remove('active');}});
  document.getElementById('d-'+key).classList.add('active');
  restart();
}}

function buildGrid(){{
  const cfg=DIFFS[cur];
  document.documentElement.style.setProperty('--cs', cfg.cs+'px');
  document.getElementById('grid').style.gridTemplateColumns='repeat('+cfg.cols+',1fr)';
  document.getElementById('remain').textContent=cfg.pairs;

  const sel=POOL.slice(0,cfg.pairs);
  deck=shuffle(sel.concat(sel.map(function(c){{return Object.assign({{}},c);}})));

  const g=document.getElementById('grid');
  g.innerHTML='';
  deck.forEach(function(c,i){{
    const el=document.createElement('div');
    el.className='card';
    el.innerHTML='<div class="inner"><div class="face back"></div>'
      +'<div class="face front"><img src="'+c.img+'" loading="lazy">'
      +'<div class="pk-name">'+c.name+'</div></div></div>';
    el.addEventListener('click', function(){{flip(el,i);}});
    g.appendChild(el);
  }});
}}

function flip(el,i){{
  if(lock||el.classList.contains('flipped')||el.classList.contains('matched')||flipped.length>=2)return;
  if(!ticker&&moves===0&&flipped.length===0){{
    ticker=setInterval(function(){{secs++;document.getElementById('timer').textContent=fmt(secs);}},1000);
  }}
  el.classList.add('flipped');
  flipped.push({{el:el,id:deck[i].id}});
  if(flipped.length===2){{
    moves++;
    document.getElementById('moves').textContent=moves;
    lock=true;
    setTimeout(check,700);
  }}
}}

function check(){{
  const a=flipped[0],b=flipped[1];
  const pairs=DIFFS[cur].pairs;
  if(a.id===b.id){{
    a.el.classList.add('matched');
    b.el.classList.add('matched');
    matched++;
    document.getElementById('matched').textContent=matched;
    document.getElementById('remain').textContent=pairs-matched;
    if(matched===pairs)setTimeout(victory,400);
  }}else{{
    [a.el,b.el].forEach(function(e){{
      e.classList.add('shake');
      setTimeout(function(){{e.classList.remove('flipped','shake');}},360);
    }});
  }}
  flipped=[];
  lock=false;
}}

function victory(){{
  clearInterval(ticker);ticker=null;
  const acc=Math.round(DIFFS[cur].pairs/moves*100);
  document.getElementById('ft').textContent=fmt(secs);
  document.getElementById('fm').textContent=moves+'회';
  document.getElementById('fa').textContent=acc+'%';
  document.getElementById('victory').classList.add('show');
}}

function restart(){{
  clearInterval(ticker);ticker=null;
  flipped=[];matched=0;moves=0;secs=0;lock=false;
  document.getElementById('timer').textContent='00:00';
  document.getElementById('moves').textContent='0';
  document.getElementById('matched').textContent='0';
  document.getElementById('victory').classList.remove('show');
  buildGrid();
}}

buildGrid();
</script>
</body></html>"""

components.html(GAME_HTML, height=900, scrolling=False)
