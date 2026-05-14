import streamlit as st
import random
import time
from .api import load_pokemon_data, save_game_log

ART_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork"

def reset_silhouette():
    st.session_state.sil_revealed = False
    st.session_state.sil_hint_count = 0
    st.session_state.sil_clear_input = True
    
    # load_pokemon_data는 @st.cache_data 덕분에 이제 매우 빠릅니다.
    pokemon_list = load_pokemon_data()
    st.session_state.sil_target = random.choice(pokemon_list)

def show_game():
    # Session state init
    if "sil_target" not in st.session_state or st.session_state.sil_target is None:
        reset_silhouette()
        # st.rerun() 대신 즉시 다음 로직으로 진행하도록 하여 불필요한 재시작 방지
    
    if "sil_revealed" not in st.session_state:
        st.session_state.sil_revealed = False
    if "sil_hint_count" not in st.session_state:
        st.session_state.sil_hint_count = 0
    if "sil_clear_input" not in st.session_state:
        st.session_state.sil_clear_input = False

    if st.session_state.get("sil_clear_input", False):
        if "guess_input" in st.session_state:
            st.session_state.guess_input = ""
        st.session_state.sil_clear_input = False

    target = st.session_state.sil_target
    # 위에서 초기화했으므로 target은 항상 존재함

    _, col_main, _ = st.columns([1, 2.2, 1])

    with col_main:
        with st.container():
            st.markdown('<div class="sil-main-card"></div>', unsafe_allow_html=True)
            st.markdown("""<div style="text-align: center; margin-bottom: 5px;"><h1 style="font-family: 'Outfit', sans-serif; font-weight: 900; font-size: 2.8rem; color: white; margin: 0; text-shadow: 0 4px 15px rgba(227, 53, 53, 0.7);">Who's That Pokémon?</h1></div>""", unsafe_allow_html=True)

            img_class = "silhouette-img" + (" revealed" if st.session_state.sil_revealed else "")
            img_url = f"{ART_URL}/{target['id']}.png"
            st.markdown(f"""<div style="text-align: center; margin: 10px 0;"><div class="image-glow-ring"><img src="{img_url}" class="{img_class}" style="width: 350px; height: 350px; object-fit: contain;"></div></div>""", unsafe_allow_html=True)

            if st.session_state.sil_revealed:
                st.markdown(f"""<div style="text-align: center; margin-bottom: 10px;"><div style="background: rgba(227, 53, 53, 0.1); border: 3px solid #E33535; border-radius: 15px; padding: 10px;"><h2 style="color: #ffffff; margin: 0; font-family: 'Outfit'; font-size: 1.8rem;">정답! {target['name'].upper()}</h2></div></div>""", unsafe_allow_html=True)
                st.button("다음 문제 보러가기 ➔", on_click=reset_silhouette, use_container_width=True)
            else:
                guess = st.text_input("포켓몬 이름 입력", placeholder="이름 입력 후 엔터...", key="guess_input", label_visibility="collapsed")

                if guess:
                    hint_used = st.session_state.sil_hint_count > 0
                    if guess.strip() == target["name"]:
                        save_game_log("silhouette", target["id"], is_correct=True, hint_used=hint_used)
                        st.balloons()
                        st.session_state.sil_revealed = True
                        st.session_state.sil_clear_input = True
                        st.rerun()
                    else:
                        save_game_log("silhouette", target["id"], is_correct=False, hint_used=hint_used, wrong_answer_name=guess.strip())
                        st.error("❌ 틀렸습니다!")
                        time.sleep(1.5)
                        st.session_state.sil_clear_input = True
                        st.rerun()

            st.write("")
            h_col1, h_col2, h_col3 = st.columns(3)
            with h_col1:
                st.markdown('<div class="btn-marker btn-hint"></div>', unsafe_allow_html=True)
                if st.button("힌트 보기", key="h_btn", use_container_width=True):
                    st.session_state.sil_hint_count += 1
                    st.rerun()
            with h_col2:
                st.markdown('<div class="btn-marker btn-giveup"></div>', unsafe_allow_html=True)
                if st.button("정답 보기", key="g_btn", use_container_width=True):
                    save_game_log("silhouette", target["id"], is_correct=False, hint_used=(st.session_state.sil_hint_count > 0), log_data={"action": "give_up"})
                    st.session_state.sil_revealed = True
                    st.rerun()
            with h_col3:
                st.markdown('<div class="btn-marker btn-next"></div>', unsafe_allow_html=True)
                if st.button("스킵 하기", key="s_btn", use_container_width=True):
                    save_game_log("silhouette", target["id"], is_correct=False, hint_used=(st.session_state.sil_hint_count > 0), log_data={"action": "skip"})
                    reset_silhouette()
                    st.rerun()

            if st.session_state.sil_hint_count > 0:
                st.write("")
                if st.session_state.sil_hint_count >= 1:
                    types = ", ".join([t["type_"]["name"] for t in target.get("types", [])])
                    st.markdown(f'<div class="sil-hint-box"><p>🧬 <b>타입:</b> {types}</p></div>', unsafe_allow_html=True)
                if st.session_state.sil_hint_count >= 2:
                    st.markdown(f'<div class="sil-hint-box"><p>🔢 <b>번호:</b> No.{target["id"]}</p></div>', unsafe_allow_html=True)
                if st.session_state.sil_hint_count >= 3:
                    st.markdown(f'<div class="sil-hint-box"><p>🔤 <b>첫 글자:</b> \'{target["name"][0]}\'</p></div>', unsafe_allow_html=True)
