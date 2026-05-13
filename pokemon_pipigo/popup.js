/**
 * Pokemon Papago - Popup UI Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const pkItems = document.querySelectorAll('.pk-item');
    const statusText = document.querySelector('.status');
    const powerSwitch = document.getElementById('power-switch');
    const fixedSwitch = document.getElementById('fixed-switch');

    // 1. 초기 상태 로드
    chrome.storage.local.get(['partner', 'isEnabled', 'isFixed'], (result) => {
        if (result.partner) {
            statusText.innerText = `현재 파트너: ${result.partner}`;
        }
        powerSwitch.checked = result.isEnabled !== false;
        fixedSwitch.checked = result.isFixed === true;
    });

    // 2. 포켓몬 파트너 변경 이벤트
    pkItems.forEach(item => {
        item.addEventListener('click', () => {
            const pokemonName = item.getAttribute('title');
            
            // 저장 및 메시지 전송
            chrome.storage.local.set({ partner: pokemonName }, () => {
                statusText.innerText = `현재 파트너: ${pokemonName}`;
                sendMessageToContent({ 
                    type: "CHANGE_PARTNER", 
                    pokemon: pokemonName 
                });
            });
        });
    });

    // 3. 온오프 토글 이벤트 (활성화)
    powerSwitch.addEventListener('change', () => {
        const isEnabled = powerSwitch.checked;
        chrome.storage.local.set({ isEnabled: isEnabled }, () => {
            sendMessageToContent({ type: "TOGGLE_POWER", isEnabled: isEnabled });
        });
    });

    // 4. 위치 고정 토글 이벤트
    fixedSwitch.addEventListener('change', () => {
        const isFixed = fixedSwitch.checked;
        chrome.storage.local.set({ isFixed: isFixed }, () => {
            sendMessageToContent({ type: "TOGGLE_FIXED", isFixed: isFixed });
        });
    });

    // 공통: 컨텐츠 스크립트에 메시지 전송
    function sendMessageToContent(message) {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0] && tabs[0].id) {
                chrome.tabs.sendMessage(tabs[0].id, message, () => {
                    if (chrome.runtime.lastError) {
                        console.log("페이지를 새로고침해야 반영됩니다.");
                    }
                });
            }
        });
    }
});
