from utils.images import ART


def get_home_html(bg: dict, chars: dict) -> str:
    return f"""
<!-- Hero -->
<div class="full-section sec-hero observer-target">
    <div class="section-inner">
        <div class="text-box reveal-up">
            <div class="sec-badge">SKN 27기 3조 프로젝트</div>
            <h1 class="sec-title">LLM, 너로 정했다!<br><b>Pokémon</b> AI 어시스턴트</h1>
            <p class="sec-desc">단순한 검색을 넘어, AI가 포켓몬 세계의 모든 것을 분석합니다.<br>전략적 배틀부터 스마트 도감, 전술적인 팀 빌딩, 실시간 AI 챗봇까지<br> 완벽한 트레이너 가이드를 경험하세요.</p>
            <a href="#explore" class="cta-btn">포켓몬 세상으로 이동</a>
        </div>
        <div class="visual-box reveal-right">
            <img src="{ART}/10199.png" class="main-artwork">
        </div>
    </div>
</div>

<!-- Pokedex -->
<div id="explore" class="full-section sec-grass observer-target">
    <div class="section-inner">
        <div class="text-box reveal-left">
            <div class="sec-badge">Infinite Knowledge</div>
            <h2 class="sec-title">전국 포켓몬 도감</h2>
            <p class="sec-desc">1세대부터 최신 세대까지 모든 포켓몬의 상세 데이터를 확인하세요. 종족값, 속성, 진화 트리를 한눈에 파악하여 배틀의 기초를 다집니다.</p>
            <a href="/pokedex" target="_self" class="cta-btn">도감 열람하기</a>
        </div>
        <div class="visual-box reveal-right">
            <img src="{ART}/1.png" class="main-artwork">
        </div>
    </div>
</div>

<!-- Battle -->
<div class="full-section sec-fire reverse observer-target">
    <div class="section-inner">
        <div class="text-box reveal-right">
            <div class="sec-badge">Simulation Arena</div>
            <h2 class="sec-title">실전 배틀 시뮬레이터</h2>
            <p class="sec-desc">치열한 배틀 현장을 시뮬레이션 하세요. 상성 분석과 정밀한 데미지 계산기를 통해 상대의 허점을 찌르는 최적의 전략을 수립할 수 있습니다.</p>
            <a href="/battle2" target="_self" class="cta-btn">배틀 시뮬레이션</a>
        </div>
        <div class="visual-box reveal-left">
            <img src="{ART}/6.png" class="main-artwork">
        </div>
    </div>
</div>

<!-- Chatbot -->
<div class="full-section sec-psychic observer-target">
    <div class="section-inner">
        <div class="text-box reveal-left">
            <div class="sec-badge">AI Assistant</div>
            <h2 class="sec-title">AI 포켓몬 박사</h2>
            <p class="sec-desc">어떤 질문이든 해결해 드립니다. 최신 메타와 랭크 배틀 통계를 학습한 AI 전문가에게 실시간으로 팀 조합과 전술을 상담받으세요.</p>
            <a href="/chatbot" target="_self" class="cta-btn">박사님과 대화하기</a>
        </div>
        <div class="visual-box reveal-right">
            <img src="{chars['obak']}" class="main-artwork">
        </div>
    </div>
</div>

<!-- Team Builder -->
<div class="full-section sec-ghost reverse observer-target">
    <div class="section-inner">
        <div class="text-box reveal-right">
            <div class="sec-badge">Strategy Lab</div>
            <h2 class="sec-title">최강 팀 빌더</h2>
            <p class="sec-desc">나만의 6마리 드림팀을 구축하고 파티의 약점을 진단하세요.<br>타입 상성을 시각적으로 분석하여 빈틈없는 스쿼드를 완성합니다.</p>
            <a href="/teambuilding" target="_self" class="cta-btn">팀 빌딩 시작</a>
        </div>
        <div class="visual-box reveal-left">
            <img src="{ART}/94.png" class="main-artwork">
        </div>
    </div>
</div>

<!-- Login -->
<div class="full-section sec-water observer-target">
    <div class="section-inner">
        <div class="text-box reveal-left">
            <div class="sec-badge">Trainer Identity</div>
            <h2 class="sec-title">나만의<br><b>트레이너 카드</b></h2>
            <p class="sec-desc">로그인하면 팀 빌딩 히스토리와 배틀 기록이 저장됩니다.<br>나만의 포켓몬 여정을 기록하고 맞춤형 AI 추천까지 받아보세요.</p>
            <a href="/login" target="_self" class="cta-btn">트레이너 등록하기</a>
        </div>
        <div class="visual-box reveal-right">
            <img src="{ART}/474.png" class="main-artwork">
        </div>
    </div>
</div>

<!-- Mini-game 1: Silhouette Quiz -->
<div class="full-section sec-electric reverse observer-target">
    <div class="section-inner">
        <div class="text-box reveal-right">
            <div class="sec-badge">Who's That Pokémon?</div>
            <h2 class="sec-title">실루엣으로 맞혀봐!<br><b>이 포켓몬은 누구게?</b></h2>
            <p class="sec-desc">흑백 실루엣만 보고 포켓몬을 맞혀보세요.<br>1세대부터 현재까지, 당신의 포켓몬 지식을 시험할 시간입니다!</p>
            <a href="/game_1" target="_self" class="cta-btn">도전 시작</a>
        </div>
        <div class="visual-box reveal-left">
            <img src="{chars['minigame1']}" class="main-artwork">
        </div>
    </div>
</div>

<!-- Mini-game 2: Rap Battle -->
<div class="full-section sec-dragon observer-target">
    <div class="section-inner">
        <div class="text-box reveal-left">
            <div class="sec-badge">Rap Battle</div>
            <h2 class="sec-title">포켓몬<br><b>랩 배틀</b></h2>
            <p class="sec-desc">포켓몬들의 치열한 언어 대결! AI가 만들어내는 랩 가사로 배틀을 펼쳐보세요.<br>누가 더 강렬한 라임을 뱉을 수 있을까요?</p>
            <a href="/game_2" target="_self" class="cta-btn">배틀 참전하기</a>
        </div>
        <div class="visual-box reveal-right">
            <img src="{chars['minigame2']}" class="main-artwork">
        </div>
    </div>
</div>

<!-- Pipigo Extension -->
<div class="full-section sec-pipigo reverse observer-target">
    <div class="section-inner">
        <div class="text-box reveal-right">
            <div class="sec-badge">New Generation Tool</div>
            <h2 class="sec-title">지능형 어시스턴트<br><b>피피고 (Pipigo)</b></h2>
            <p class="sec-desc">당신의 웹 브라우저 속에 귀여운 포켓몬 파트너가 나타납니다!<br> 지금 바로 경험해 보세요.</p>
            <a href="https://chromewebstore.google.com/search/%ED%94%BC%ED%94%BC%EA%B3%A0?hl=ko" target="_blank" class="cta-btn">웹 스토어에서 보기</a>
        </div>
        <div class="visual-box reveal-left">
            <img src="{chars['pipigo']}" class="main-artwork" style="border-radius: 40px; box-shadow: 0 20px 50px rgba(0,0,0,0.5);">
        </div>
    </div>
</div>

<div style="padding:50px 5% 60px; text-align:center; background:#000; color:rgba(255,255,255,0.3); font-size:13px; font-family:'Inter',sans-serif; letter-spacing:1px; border-top:1px solid rgba(255,255,255,0.03);">
    © 2026 POKÉMON AI ASSISTANT. ALL RIGHTS RESERVED.<br>
    <span style="display:inline-block; margin-top:10px; opacity:0.6;">새로운 시대를 탐험하는 트레이너를 위한 지능형 가이드 · Powered by Advanced AI</span>
</div>
"""


def get_home_js() -> str:
    return """
<script>
    const parentDoc = window.parent.document;

    // Scroll snap + dynamic height
    const snapContainer = parentDoc.querySelector('.main') || parentDoc.querySelector('[data-testid="stAppViewContainer"]');
    if (snapContainer) {
        snapContainer.style.scrollSnapType = 'y mandatory';
        snapContainer.style.overflowY = 'scroll';
    }

    function applySnapHeights() {
        const vh = window.parent.innerHeight;
        parentDoc.querySelectorAll('.full-section').forEach(el => {
            el.style.height = vh + 'px';
            el.style.scrollSnapAlign = 'start';
            el.style.scrollSnapStop = 'always';
        });
    }

    applySnapHeights();
    window.parent.addEventListener('resize', applySnapHeights);

    // Reveal animation trigger
    setTimeout(() => { parentDoc.body.classList.add('js-ready'); }, 100);

    // IntersectionObserver for scroll reveals
    const scrollContainer = parentDoc.querySelector('.main') || parentDoc.querySelector('[data-testid="stAppViewContainer"]');
    const targets = parentDoc.querySelectorAll('.observer-target');

    if (scrollContainer && targets.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => { if (entry.isIntersecting) entry.target.classList.add('in-view'); });
        }, { root: scrollContainer, threshold: 0.05, rootMargin: '0px 0px -50px 0px' });

        targets.forEach(t => observer.observe(t));

        scrollContainer.addEventListener('scroll', () => {
            targets.forEach(t => {
                if (t.getBoundingClientRect().top < window.innerHeight - 100) t.classList.add('in-view');
            });
        }, { passive: true });
    }

    // Click-to-catch decor sprites
    const pokeIds = [1,4,7,25,39,52,54,58,63,65,74,92,94,130,133,143,149,150,151,172,197,212,248,373,448,700];
    parentDoc.querySelectorAll('.decor-sprite').forEach(sprite => {
        sprite.style.pointerEvents = 'auto';
        sprite.addEventListener('click', function() {
            const id = pokeIds[Math.floor(Math.random() * pokeIds.length)];
            this.style.opacity = '0';
            setTimeout(() => {
                this.src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/' + id + '.gif';
                this.style.opacity = '0.8';
            }, 250);
        });
    });
</script>
"""
