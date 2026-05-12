/**
 * Pokemon Papago - Content Script
 */

(function() {
    console.log("Pokemon Papago Phase 2 Loaded!");

    let currentPartner = "피카츄(냠냠)";
    const PK_IMG_MAP = {
        "피카츄(냠냠)": chrome.runtime.getURL("img/1.gif"),
        "야돈(콧물)": chrome.runtime.getURL("img/2.gif"),
        "리자몽(비행)": chrome.runtime.getURL("img/3.gif"),
        "꼬부기(당당)": chrome.runtime.getURL("img/4.gif")
    };

    // 1. UI 엘리먼트 생성
    const container = document.createElement('div');
    container.className = 'pk-papago-container';
    container.style.display = 'none'; // 초기엔 숨김 (상태 확인 후 표시)

    const pokemonImg = document.createElement('img');
    pokemonImg.className = 'pk-papago-img';

    const bubble = document.createElement('div');
    bubble.className = 'pk-papago-bubble';
    bubble.innerHTML = `
        <div class="pk-papago-input-wrapper">
            <input type="text" class="pk-papago-input" placeholder="피피고에게 물어보기">
        </div>
        <div class="pk-papago-result"></div>
    `;

    container.appendChild(bubble);
    container.appendChild(pokemonImg);
    document.body.appendChild(container);

    // 초기 상태 로드
    chrome.storage.local.get(['partner', 'isEnabled', 'isFixed'], (result) => {
        if (result.partner && PK_IMG_MAP[result.partner]) {
            currentPartner = result.partner;
            refreshGif();
        } else {
            pokemonImg.src = `${PK_IMG_MAP["피카츄(냠냠)"]}?t=${Date.now()}`;
        }

        // 온오프 및 고정 상태 반영
        const isEnabled = result.isEnabled !== false;
        container.style.display = isEnabled ? 'block' : 'none';
        isFixed = result.isFixed === true;
    });

    // 2. 메시지 리스너 (팝업/백그라운드 통신)
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.type === "CHANGE_PARTNER") {
            currentPartner = request.pokemon;
            refreshGif();
            
            // 변경 효과
            pokemonImg.style.filter = "brightness(2) contrast(2)";
            setTimeout(() => pokemonImg.style.filter = "drop-shadow(0 5px 20px rgba(0,0,0,0.15))", 500);
        }
        else if (request.type === "TOGGLE_POWER") {
            container.style.display = request.isEnabled ? 'block' : 'none';
            if (request.isEnabled) refreshGif();
        }
        else if (request.type === "TOGGLE_FIXED") {
            isFixed = request.isFixed;
            if (isFixed) {
                targetX = currentX;
                targetY = currentY;
            }
        }
    });

    // GIF 강제 재시작 함수
    function refreshGif() {
        const baseUrl = PK_IMG_MAP[currentPartner] || PK_IMG_MAP["피카츄(냠냠)"];
        pokemonImg.src = `${baseUrl}?t=${Date.now()}`;
    }

    // 8초마다 강제로 GIF 깨우기 (무한 반복 보장)
    setInterval(() => {
        if (container.style.display !== 'none' && !isDragging) {
            refreshGif();
        }
    }, 8000);

    const inputField = bubble.querySelector('.pk-papago-input');
    const resultArea = bubble.querySelector('.pk-papago-result');

    // 4. 클릭 이벤트: 말풍선 토글
    pokemonImg.addEventListener('click', () => {
        refreshGif();
        const isVisible = bubble.style.display === 'block';
        bubble.style.display = isVisible ? 'none' : 'block';
        if (!isVisible) {
            inputField.focus();
            resultArea.style.display = 'none';
            inputField.value = '';
        }
    });

    // 5. 엔터 키 이벤트: Background script와 통신
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const text = inputField.value.trim();
            if (!text) return;

            inputField.disabled = true;
            resultArea.style.display = 'block';
            resultArea.innerText = '답변 생성중...';
            resultArea.classList.add('thinking');

            chrome.runtime.sendMessage({
                type: "TRANSLATE",
                text: text,
                pokemon: currentPartner
            }, (response) => {
                inputField.disabled = false;
                resultArea.classList.remove('thinking');
                
                if (response && response.success) {
                    resultArea.innerText = response.result;
                } else {
                    resultArea.innerText = "번역에 실패했다옹! 다시 시도해라옹.";
                }
            });
        }
    });

    // 6. 드래그 앤 드롭 기능
    let isDragging = false;
    let offsetX, offsetY;

    container.addEventListener('mousedown', (e) => {
        if (e.target === pokemonImg) {
            isDragging = true;
            const rect = container.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            container.style.transition = 'none';
        }
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const x = e.clientX - offsetX;
        const y = e.clientY - offsetY;
        
        container.style.left = `${x}px`;
        container.style.top = `${y}px`;
        container.style.bottom = 'auto';
        container.style.right = 'auto';
    });

    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            container.style.cursor = 'pointer';
        }
    });

    // 7. 지능형 물리 엔진 (보행 및 시선 처리)
    let currentX = window.innerWidth - 150;
    let currentY = window.innerHeight - 150;
    let targetX = currentX;
    let targetY = currentY;
    let walkSpeed = 1.2;
    let isFixed = false; // 위치 고정 상태

    // 마우스 위치 추적 (시선 처리)
    document.addEventListener('mousemove', (e) => {
        if (!isDragging && bubble.style.display !== 'block') {
            const centerX = currentX + 60;
            if (e.clientX < centerX) {
                pokemonImg.style.transform = "scaleX(1)"; // 왼쪽 보기
            } else {
                pokemonImg.style.transform = "scaleX(-1)"; // 오른쪽 보기
            }
        }
    });

    // 부드러운 이동 루프
    function updatePhysics() {
        if (!isDragging && bubble.style.display !== 'block' && !isFixed) {
            const dx = targetX - currentX;
            const dy = targetY - currentY;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance > 5) {
                currentX += (dx / distance) * walkSpeed;
                currentY += (dy / distance) * walkSpeed;
                
                container.style.left = `${currentX}px`;
                container.style.top = `${currentY}px`;
                container.style.bottom = 'auto';
                container.style.right = 'auto';

                // 걷는 방향으로 몸 돌리기
                pokemonImg.style.transform = dx < 0 ? "scaleX(1)" : "scaleX(-1)";
            } else {
                // 도착하면 즉시 새로운 목표 설정 (무한 반복 산책)
                targetX = Math.max(50, Math.min(window.innerWidth - 150, currentX + (Math.random() - 0.5) * 600));
                targetY = Math.max(50, Math.min(window.innerHeight - 150, currentY + (Math.random() - 0.5) * 500));
            }
        } else if (isDragging) {
            currentX = container.getBoundingClientRect().left;
            currentY = container.getBoundingClientRect().top;
            targetX = currentX;
            targetY = currentY;
        }
        requestAnimationFrame(updatePhysics);
    }

    requestAnimationFrame(updatePhysics);

})();
