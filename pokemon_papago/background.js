/**
 * Pokemon Papago - Background Service Worker (Groq Version)
 */

// @ENV_START (update_pokemon_env.py에 의해 자동 관리됩니다)
const NAVER_CLIENT_ID = "aifel09hgb";
const NAVER_CLIENT_SECRET = "afPNkdaylYbTWabHyot0ZYCaSvDKwqbNhEHLyjE9";
const GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE";
// @ENV_END

const TONE_FILTERS = {
    // 말투 필터를 사용하지 않음 (원본 텍스트 그대로 반환)
};

// 2. 메시지 리스너
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "TRANSLATE") {
        handleTranslation(request, sendResponse);
        return true; 
    }
});

// 3. Groq AI 번역 실행
async function handleTranslation(request, sendResponse) {
    try {
        const { text, pokemon } = request;

        if (!GROQ_API_KEY || GROQ_API_KEY.startsWith("YOUR")) {
            throw new Error("Groq API 키가 설정되지 않았습니다.");
        }

        // Groq API 호출 (OpenAI 호환)
        const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${GROQ_API_KEY}`
            },
            body: JSON.stringify({
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are 'Pipigo', a brilliant Pokemon AI assistant. Your mission is to help users understand web content. 1) If the input is a sentence/phrase, provide the most natural and context-aware translation (KO<->EN). 2) If the input is a question, answer it intelligently. 3) Keep your response concise, helpful, and friendly. Don't be a robot; be a smart partner who understands the web."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "temperature": 0.3
            })
        });

        const responseText = await response.text();
        
        if (!response.ok) {
            console.error("Groq Error Response:", responseText);
            throw new Error(`Groq API 호출 실패 (${response.status})`);
        }

        const data = JSON.parse(responseText);
        const translatedText = data.choices[0].message.content.trim();

        // 말투 필터 적용
        const filter = TONE_FILTERS[pokemon] || ((t) => t);
        const result = filter(translatedText);

        sendResponse({ success: true, result: result });

    } catch (error) {
        console.error("Translation Error:", error);
        sendResponse({ success: false, error: error.message });
    }
}
