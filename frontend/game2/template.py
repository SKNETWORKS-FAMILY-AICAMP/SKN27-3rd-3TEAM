import json

ARTWORK = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"

POKEMON_POOL = [
    (1, "이상해씨"), (4, "파이리"),    (7, "꼬부기"),   (25, "피카츄"),
    (39, "푸린"),    (52, "나옹"),     (54, "고라파덕"), (94, "팬텀"),
    (131, "라프라스"),(133, "이브이"), (143, "잠만보"), (149, "망나뇽"),
    (150, "뮤츠"),   (6, "리자몽"),    (9, "거북왕"),
]

def get_game_html(char_img, pool_json):
    return f"""<!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:transparent;font-family:'Outfit',sans-serif;color:#fff;overflow:hidden}}
    #wrap{{max-width:100%;margin:0 auto;padding:5px}}

    #title{{text-align:center;margin-bottom:12px;margin-top:2px}}
    #title h1{{font-size:1.6rem;font-weight:900;
      background:linear-gradient(90deg,#FF88FF,#88FFFF);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow: 0 4px 15px rgba(140, 0, 255, 0.3);}}
    #title p{{color:#ccc;font-size:0.8rem;margin-top:2px;opacity:0.8}}

    #diff-bar{{display:flex;gap:8px;margin-bottom:12px}}
    .diff-btn{{flex:1;padding:8px 5px;background:rgba(20,20,20,0.6);
      border:2px solid rgba(255,255,255,0.1);border-radius:12px;cursor:pointer;
      text-align:center;transition:all .3s;backdrop-filter:blur(10px)}}
    .diff-btn:hover{{border-color:rgba(140,0,255,0.6);background:rgba(140,0,255,0.1)}}
    .diff-btn.active{{border-color:#BC66FF;box-shadow:0 0 20px rgba(188,102,255,0.25);
      background:rgba(140,0,255,0.2)}}
    .diff-label{{font-size:.9rem;font-weight:900;color:#fff;}}
    .diff-sub{{font-size:.65rem;color:#ccc;margin-top:2px}}

    #stats{{display:flex;justify-content:space-around;background:rgba(0,0,0,0.5);
      border:1px solid rgba(188,102,255,0.2);border-radius:18px;padding:12px;margin-bottom:15px;
      backdrop-filter:blur(10px);box-shadow:0 10px 30px rgba(0,0,0,0.5)}}
    .stat{{text-align:center}}
    .slabel{{font-size:.6rem;color:#ccc;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;font-weight:800}}
    .sval{{font-size:1.4rem;font-weight:900;color:#fff;font-family:monospace;
      text-shadow: 0 0 10px rgba(188,102,255,0.8), 0 0 20px rgba(188,102,255,0.4);
      letter-spacing:1px}}

    :root{{--cw:90px}}
    #grid{{display:grid;gap:10px;justify-items:center;margin-bottom:15px}}
    .card{{width:var(--cw);height:calc(var(--cw) * 1.4);perspective:1000px;cursor:pointer}}
    .inner{{width:100%;height:100%;position:relative;transform-style:preserve-3d;
      transition:transform .5s cubic-bezier(.4,0,.2,1);border-radius:10px}}
    .card.flipped .inner,.card.matched .inner{{transform:rotateY(180deg)}}
    .card.matched .inner{{box-shadow:0 0 15px rgba(0,255,204,0.5);border-radius:10px}}
    
    .face{{position:absolute;width:100%;height:100%;backface-visibility:hidden;
      border-radius:10px;display:flex;align-items:center;justify-content:center;overflow:hidden;
      border:1px solid rgba(255,255,255,0.15)}}
    
    .back{{background:linear-gradient(135deg,#2e005e,#14002e);
      box-shadow:inset 0 0 20px rgba(188,102,255,0.2)}}
    .back::after{{content:'';width:100%;height:100%;
      background:url('{char_img}') center/cover no-repeat;
      opacity:.85;filter:brightness(0.9)}}
    
    .front{{background:radial-gradient(circle at center, #1a1a1a, #0a0a0a);
      transform:rotateY(180deg)}}
    .front img{{width:95%;height:95%;object-fit:contain;padding:5px;
      filter:drop-shadow(0 5px 10px rgba(0,0,0,0.6))}}
    
    .pk-name{{position:absolute;bottom:0;left:0;width:100%;font-size:9px;font-weight:900;
      color:#BC66FF;text-align:center;background:rgba(0,0,0,0.7);padding:3px 0;
      backdrop-filter:blur(5px);border-bottom-left-radius:8px;border-bottom-right-radius:8px}}

    #restart{{display:block;width:100%;padding:10px;margin-top:5px;
      background:linear-gradient(90deg,#9D50BB,#6E48AA);color:#fff;
      border:none;border-radius:10px;font-size:0.9rem;font-weight:900;cursor:pointer;
      box-shadow:0 4px 15px rgba(110,72,170,0.4);transition:all .3s;letter-spacing:1px;
      text-transform:uppercase;border:1px solid rgba(255,255,255,0.1)}}
    #restart:hover{{transform:translateY(-2px);box-shadow:0 8px 25px rgba(110,72,170,0.6);filter:brightness(1.1)}}

    #victory{{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.9);z-index:9999;
      align-items:center;justify-content:center;backdrop-filter:blur(20px);
      -webkit-backdrop-filter:blur(20px)}}
    #victory.show{{display:flex}}
    #vcard{{background:rgba(30,30,30,0.9);border:2px solid #BC66FF;border-radius:25px;
      padding:30px;text-align:center;max-width:350px;width:90%;
      box-shadow:0 0 80px rgba(188,102,255,0.3);animation:pop .6s cubic-bezier(.34,1.56,.64,1)}}
    @keyframes pop{{from{{transform:scale(.7);opacity:0}}to{{transform:scale(1);opacity:1}}}}
    #vcard h2{{font-size:2.2rem;font-weight:900;color:#fff;margin-bottom:12px}}
    .vstats{{color:#ccc;font-size:.9rem;margin:12px 0 20px;line-height:2}}
    .vstats span{{color:#BC66FF;font-weight:900;font-size:1.1rem}}
    #play-again{{padding:12px 40px;background:#BC66FF;
      color:#fff;border:none;border-radius:50px;font-size:1rem;font-weight:900;
      cursor:pointer;transition:all .3s;box-shadow:0 8px 25px rgba(188,102,255,0.4)}}
    #play-again:hover{{transform:scale(1.05);box-shadow:0 12px 35px rgba(188,102,255,0.6)}}
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
          <div class="diff-sub">4×3 &middot; 6쌍</div>
        </div>
        <div class="diff-btn active" id="d-normal" onclick="setDiff('normal')">
          <div class="diff-label">보통</div>
          <div class="diff-sub">4×4 &middot; 8쌍</div>
        </div>
        <div class="diff-btn" id="d-hard" onclick="setDiff('hard')">
          <div class="diff-label">어려움</div>
          <div class="diff-sub">6×5 &middot; 15쌍</div>
        </div>
      </div>

      <div id="stats">
        <div class="stat"><div class="slabel">⏱ 시간</div><div class="sval" id="timer">00:00</div></div>
        <div class="stat"><div class="slabel">시도 횟수</div><div class="sval" id="moves">0</div></div>
        <div class="stat"><div class="slabel">맞춘 쌍</div><div class="sval" id="matched">0</div></div>
        <div class="stat"><div class="slabel">남은 쌍</div><div class="sval" id="remain">-</div></div>
      </div>

      <div id="grid"></div>
      <button id="restart" onclick="restart()">다시 시작</button>
    </div>

    <div id="victory">
      <div id="vcard">
        <h2>클리어!</h2>
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
      easy:   {{cols:4, pairs:6,  cw:110}},
      normal: {{cols:4, pairs:8,  cw:90}},
      hard:   {{cols:6, pairs:15, cw:70}},
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
      document.documentElement.style.setProperty('--cw', cfg.cw+'px');
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
