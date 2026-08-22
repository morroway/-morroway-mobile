from __future__ import annotations
import os, json
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from engine import *
from models import *
from storage import save_post, save_metrics, posts_df, performance_df, backend_name, export_all
from top100_lab import read_benchmark_upload, benchmark_prompt_payload, save_style_profile, load_style_profile

load_dotenv()
ROOT=Path(__file__).parent

def find_file(name, subdir=""):
    p=ROOT/name
    if p.exists(): return p
    if subdir:
        p2=ROOT/subdir/name
        if p2.exists(): return p2
    return p

ASSET=find_file("morroway_home.png","assets")
ICON_PATH=find_file("morroway_icon.png","assets")
ICON=Image.open(ICON_PATH) if ICON_PATH.exists() else "📻"
APP_VERSION="MORROWAY MOBILE v1.5 · PEOPLE FIRST EDITORIAL"

st.set_page_config(page_title="오늘도 한살 편집국",page_icon=ICON,layout="centered",initial_sidebar_state="collapsed")

MOBILE_CSS="""
<style>
:root { --cream:#FAF6EC; --ink:#202322; --teal:#6F9FA1; --coral:#D96C4B; --olive:#41533B; --sand:#F0E9D9; --navy:#171923; }
html, body, [class*="css"] { font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif; }
.stApp { background: radial-gradient(circle at 50% 0%, #fffaf0 0%, var(--cream) 42%, #f7f1e3 100%); color:var(--ink); }
.block-container { max-width: 680px; padding-top:.55rem; padding-bottom:6rem; padding-left:.9rem; padding-right:.9rem; }
[data-testid="stHeader"] { background: rgba(250,246,236,.80); }
[data-testid="stSidebar"] { display:none; }
#MainMenu, footer { visibility:hidden; }
.hero-kicker { text-align:center; color:#6b6b64; font-size:.82rem; margin-bottom:.45rem; }
.hero-title { text-align:center; font-size:1.06rem; font-weight:800; margin:.65rem 0 .15rem; }
.hero-sub { text-align:center; font-size:.9rem; color:#62635f; margin-bottom:.9rem; line-height:1.5; }
.hero-logo img { border-radius:26px !important; box-shadow:0 14px 38px rgba(73,67,50,.12); border:1px solid rgba(111,159,161,.25); }
.stButton>button { width:100%; min-height:3.45rem; border-radius:17px; border:1px solid rgba(57,72,63,.16); font-weight:800; font-size:1rem; box-shadow:0 5px 14px rgba(70,60,45,.06); background:#171923 !important; color:#FFFFFF !important; opacity:1 !important; text-shadow:none !important; }
.stButton>button p, .stButton>button span { color:#FFFFFF !important; opacity:1 !important; font-weight:800 !important; }
.stButton>button:hover { border-color:rgba(217,108,75,.65) !important; color:#FFFFFF !important; }
.stButton>button:focus { color:#FFFFFF !important; }
[data-testid="stButton"] button:disabled, .stButton>button:disabled { background:#D8D3C8 !important; color:#67645F !important; opacity:1 !important; }
.stButton>button[kind="primary"] { background:var(--coral) !important; border-color:var(--coral) !important; color:#ffffff !important; }
.stButton>button:disabled { background:#d8d3c8 !important; color:#777 !important; }
[data-testid="stLinkButton"] a { background:var(--navy) !important; color:#fff !important; border-radius:17px !important; font-weight:760 !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:20px; border-color:rgba(65,83,59,.14) !important; background:rgba(255,255,255,.52); }
[data-testid="stMetric"] { background:rgba(255,255,255,.62); padding:.62rem .65rem; border-radius:16px; border:1px solid rgba(65,83,59,.10); }
textarea, input { font-size:16px !important; }
.small-note { font-size:.81rem; color:#77756d; line-height:1.55; }
.pill { display:inline-block; margin:.12rem .2rem .12rem 0; padding:.26rem .52rem; border-radius:999px; background:#edf3ef; color:#425549; font-size:.76rem; font-weight:650; }
.pill.coral { background:#f8e2d9; color:#9c4b33; }
.pill.blue { background:#e1eeee; color:#436f73; }
.pill.gold { background:#f2e8c7; color:#745f20; }
.pill.free { background:#e5f3e8; color:#2c6b3d; }
.pill.paid { background:#f6e3dd; color:#a34e36; }
.score-line { color:#62635f; font-size:.82rem; margin-top:.25rem; }
.brand-rule { border-top:1px solid rgba(111,159,161,.35); margin:1rem 0; }
.mobile-card-title { font-size:1.04rem; font-weight:820; line-height:1.45; margin-bottom:.32rem; }
.mobile-card-body { color:#33362f; line-height:1.62; font-size:.92rem; }
.action-card { padding:.9rem 1rem; border-radius:18px; background:#fffdf7; border:1px solid rgba(31,38,38,.12); margin:.45rem 0; box-shadow:0 4px 14px rgba(70,60,45,.04); }
.action-card b { color:#171923; }
.dna-box { padding:.9rem 1rem; border-radius:18px; background:linear-gradient(135deg,#eef5f2,#fff7e9); border:1px solid rgba(111,159,161,.28); margin:.55rem 0 .9rem; line-height:1.62; color:#30352f; }
.visual-box { padding:.8rem .95rem; border-radius:16px; background:#f4efe3; border-left:4px solid #6F9FA1; margin:.45rem 0 .8rem; line-height:1.55; color:#343632; }
.copy-hint { padding:.7rem .85rem; border-radius:14px; background:#edf3ef; color:#365044; font-size:.86rem; line-height:1.5; margin:.45rem 0; }
.section-title { font-size:1.28rem; font-weight:850; margin:.15rem 0 .15rem; }
.section-sub { color:#6b6c66; font-size:.87rem; margin-bottom:.9rem; }
.modebox { padding:.78rem .9rem; border-radius:16px; background:#fff8e9; border:1px solid #eadfc4; margin:.5rem 0 .8rem; font-size:.86rem; line-height:1.5; }
.freebox { padding:.78rem .9rem; border-radius:16px; background:#eef7ef; border:1px solid #cee4d2; margin:.5rem 0 .8rem; font-size:.86rem; line-height:1.5; }
.paidbox { padding:.78rem .9rem; border-radius:16px; background:#fff0ea; border:1px solid #eccdc0; margin:.5rem 0 .8rem; font-size:.86rem; line-height:1.5; }
@media (max-width:480px) {
 .block-container { padding-left:.72rem; padding-right:.72rem; padding-top:.28rem; }
 .stButton>button { min-height:3.45rem; font-size:.96rem; }
 [data-testid="stMetricValue"] { font-size:1.15rem; }
 .hero-logo img { border-radius:22px !important; }
}
</style>
"""
st.markdown(MOBILE_CSS,unsafe_allow_html=True)

# ---------- session ----------
def init_state():
    defaults={
        "page":"home","work_mode":"🆓 무료 편집","model_mode":"절약","board":None,"research":"","sources":[],
        "candidate":None,"draft":None,"final_hook":"","final_body":"","final_closing":"","final_question":"",
        "last_saved_id":None,"quick_category":"오늘의 기억","api_calls":0,"free_prompt":"","free_prompt_title":"",
        "affiliate_on":False,"current_issue":"","issue_url":"",
        "omni_topic":"","omni_category":"오늘의 기억","omni_raw":"","omni_sections":{},"omni_candidate":None,
        "editorial_mode":"설명형 에디토리얼","visual_mode":"설명+그리움 하이브리드","generation_bridge":"세대 연결형",
    }
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v
init_state()

def go(page): st.session_state.page=page

def count_api(n=1): st.session_state.api_calls=st.session_state.get("api_calls",0)+n

def page_header(title,sub="",back=True):
    c1,c2=st.columns([1,5])
    if back and c1.button("←",key=f"back_{title}"):
        go("home"); st.rerun()
    with c2:
        st.markdown(f'<div class="section-title">{title}</div>',unsafe_allow_html=True)
        if sub: st.markdown(f'<div class="section-sub">{sub}</div>',unsafe_allow_html=True)

def api_ready(): return bool(get_api_key())
def selected_model(): return get_model(st.session_state.get("model_mode","절약"))
def cheap_model(): return get_model("절약")
def is_free(): return st.session_state.get("work_mode","🆓 무료 편집").startswith("🆓")

def mode_selector(key):
    mode=st.radio("생성 방식",["🆓 무료 편집","⚡ AI 자동"],index=0 if is_free() else 1,horizontal=True,key=key)
    st.session_state.work_mode=mode
    if mode.startswith("🆓"):
        st.markdown('<div class="freebox"><b>API 비용 0원.</b> 앱이 소재·후킹 구조·질문을 정리하고, 완성 프롬프트를 만들어 ChatGPT에서 마무리합니다.</div>',unsafe_allow_html=True)
    else:
        st.markdown('<div class="paidbox"><b>OpenAI API 사용.</b> 앱 안에서 바로 완성합니다. 기본은 절약 모델, 웹검색은 꼭 필요할 때만 켜세요.</div>',unsafe_allow_html=True)
    return mode

def source_markdown(sources):
    if not sources: st.caption("웹 조사 출처 없음")
    for i,s in enumerate(sources,1): st.markdown(f"{i}. [{s.get('title') or s.get('url')}]({s.get('url')})")

def current_final_text():
    d=ThreadDraft.model_validate(st.session_state.draft) if st.session_state.get("draft") else None
    return build_final_text(
        st.session_state.get("final_hook",d.hooks[0] if d else ""),
        st.session_state.get("final_body",d.body if d else ""),
        st.session_state.get("final_closing",d.closing_line if d else ""),
        st.session_state.get("final_question",d.discussion_questions[0] if d else ""),
        d.topic_tag if d else "",st.session_state.get("affiliate_on",False))

def load_draft(d:ThreadDraft):
    st.session_state.draft=d.model_dump(); st.session_state.final_hook=d.hooks[0]; st.session_state.final_body=d.body
    st.session_state.final_closing=d.closing_line; st.session_state.final_question=d.discussion_questions[0] if d.discussion_questions else ""
    st.session_state.writer_hook_edit=d.hooks[0]; st.session_state.writer_body_edit=d.body; st.session_state.writer_closing_edit=d.closing_line
    st.session_state.writer_question_edit=d.discussion_questions[0] if d.discussion_questions else ""; st.session_state.page="writer"

def show_free_prompt(title,prompt,chatgpt=True):
    st.markdown(f"### 📋 {title}")
    st.caption("아래 코드블록 오른쪽의 복사 아이콘 → ChatGPT 앱에 붙여넣기. 이 단계는 OpenAI API 크레딧을 쓰지 않습니다.")
    st.code(prompt,language=None)
    if chatgpt: st.link_button("ChatGPT 열기 ↗","https://chatgpt.com/",use_container_width=True)

# ---------- HOME ----------
def render_home():
    today=korea_today()
    st.markdown(f'<div class="hero-kicker">{today.strftime("%Y.%m.%d")} · 오늘도 한살 편집국</div>',unsafe_allow_html=True)
    if ASSET.exists():
        st.markdown('<div class="hero-logo">',unsafe_allow_html=True); st.image(str(ASSET),use_container_width=True); st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="hero-title">정보는 또렷하게, 재미는 재치 있게, 사람은 끝까지 중심에.</div>',unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">궁금해서 멈추고 · 알아서 남고 · 이야기하고 싶어지고 · 오래 보면 삶에 조금 도움이 되는 생활교양.</div>',unsafe_allow_html=True)
    st.markdown('<span class="pill free">🆓 무료 기본</span><span class="pill paid">⚡ 자동은 선택</span>',unsafe_allow_html=True)

    if st.button("✨ 한 소재로 5채널 + 이미지",type="primary",key="home_omni"):
        go("studio"); st.rerun()
    a,b=st.columns(2)
    if a.button("🔥 오늘 뭐 쓰지",key="home_ideas"): go("ideas"); st.rerun()
    if b.button("💬 댓글·답글",key="home_talk"): go("talk"); st.rerun()
    if st.button("📊 성과·수익 보기",key="home_metrics"): go("metrics"); st.rerun()

    with st.expander("고급 도구 · 필요할 때만"):
        a,b=st.columns(2)
        if a.button("✍️ Threads만 빠르게",key="home_quick"): go("quick"); st.rerun()
        if b.button("💰 수익경로 진단",key="home_money"): go("money"); st.rerun()
        a,b=st.columns(2)
        if a.button("🔁 기존 글 확장",key="home_expand"): go("expand"); st.rerun()
        if b.button("⚙️ 설정·TOP100",key="home_settings"): go("settings"); st.rerun()

    if api_ready(): st.success(f"API 연결됨 · 무료모드에서는 사용하지 않음 · 이번 세션 자동 호출 {st.session_state.api_calls}회")
    else: st.info("API 키가 없어도 핵심 무료 편집실은 정상 작동합니다.")
    st.markdown('<div class="dna-box"><b>MORROWAY 편집헌장</b><br>사람의 존엄 · 민주적 대화 · 평등 · 공동체 · 낮은 곳의 시선 · 모든 일의 가치.<br>재치 있게 시작하되 누군가를 낮추지 않고, 사실은 또렷하게, 결론은 사람 쪽으로 돌아옵니다.</div>',unsafe_allow_html=True)

# ---------- IDEAS ----------
def render_ideas():
    page_header("🔥 오늘 뭐 쓰지","무료모드에서는 기념일·계절·상시형 저널을 사용하고, 최신 이슈는 한 줄만 붙여넣습니다.")
    mode=mode_selector("ideas_mode")
    target=st.date_input("기준일",value=korea_today(),key="ideas_date").isoformat()
    pattern=st.selectbox("오늘의 편집판",list(JOURNAL_PATTERNS),index=1,key="ideas_pattern")
    cats=st.multiselect("관심 카테고리",CATEGORIES,default=CATEGORIES,key="ideas_cats")
    manual=st.text_input("오늘 특별히 보고 싶은 것",placeholder="예: 서울 지명, 90년대 직장문화, 부모님 여름 건강",key="ideas_manual")
    n=st.slider("후보 수",3,8,5,key="ideas_n")

    if mode.startswith("🆓"):
        issue=st.text_input("🔥 오늘 본 이슈 한 줄 (선택)",placeholder="예: 오늘 폭염특보 확대 / 기사 제목 한 줄",key="free_issue")
        url=st.text_input("기사 URL (선택)",placeholder="https://...",key="free_issue_url")
        if issue:
            with st.expander("이 최신 이슈를 무료로 쓰는 방법",expanded=False):
                show_free_prompt("최신 이슈 → ChatGPT 편집 프롬프트",free_issue_prompt(issue,url,target))
        if st.button("🗞️ 무료 추천 만들기 · API 0원",type="primary",key="free_board"):
            if not cats: st.error("카테고리를 하나 이상 골라주세요.")
            else:
                st.session_state.board=free_candidate_board(target,cats,JOURNAL_PATTERNS[pattern],manual,n).model_dump()
                st.session_state.research="무료모드: 웹검색 미사용"; st.session_state.sources=[]
    else:
        use_web=st.toggle("최신 웹 조사 (비용 증가)",False,key="ideas_web")
        st.caption("절약팁: 후보 탐색은 Luna를 사용하고, 후보 3~5개면 충분합니다.")
        if st.button("⚡ AI 추천 만들기",type="primary",key="paid_board"):
            if not api_ready(): st.error("API Key가 필요합니다. 무료모드는 키 없이 사용 가능합니다.")
            elif not cats: st.error("카테고리를 하나 이상 골라주세요.")
            else:
                try:
                    cal=calendar_context(target); research="웹검색 미사용. 최신 사실은 단정하지 않는다."; sources=[]
                    with st.spinner("절약형 편집회의 중…"):
                        if use_web:
                            research,sources=web_research(research_prompt(target,cats,JOURNAL_PATTERNS[pattern],manual,cal),cheap_model()); count_api(1)
                        board=parse_model(CandidateBoard,board_prompt(target,cats,JOURNAL_PATTERNS[pattern],manual,research,sources,min(n,5)),cheap_model()); count_api(1)
                    st.session_state.board=board.model_dump(); st.session_state.research=research; st.session_state.sources=sources
                except Exception as e: st.error(f"생성 오류: {e}")

    if st.session_state.get("board"):
        board=CandidateBoard.model_validate(st.session_state.board); st.info(board.editorial_note)
        for i,cand in enumerate(board.candidates,1):
            with st.container(border=True):
                st.markdown(f'<div class="mobile-card-title">{i}. {cand.curiosity_hook}</div>',unsafe_allow_html=True)
                st.markdown(f'<span class="pill blue">{cand.category}</span><span class="pill">{cand.asset_role}</span><span class="pill coral">추천 {cand.suggested_goal}</span>',unsafe_allow_html=True)
                st.markdown(f'<div class="mobile-card-body">{cand.why_now}<br><b>댓글 방아쇠:</b> {cand.conversation_trigger}</div>',unsafe_allow_html=True)
                st.markdown(f'<div class="score-line">👀 {cand.reach_score} · 💬 {cand.conversation_score} · ❓ {cand.curiosity_score} · 🔖 {cand.save_score} · 💰 {cand.monetization_score} · ⚠️ {cand.fact_risk}</div>',unsafe_allow_html=True)
                if st.button("이 소재로 5채널 만들기",key=f"pick_{i}",use_container_width=True):
                    st.session_state.candidate=cand.model_dump(); st.session_state.omni_candidate=cand.model_dump(); st.session_state.omni_topic=cand.topic; st.session_state.omni_category=cand.category; go("studio"); st.rerun()
        if st.session_state.get("sources"):
            with st.expander("🔎 유료 웹 조사 출처"): source_markdown(st.session_state.sources)

# ---------- COMPOSE ----------
def render_compose():
    page_header("✍️ 글의 목적 고르기","무료면 프롬프트를 복사하고, 자동이면 앱 안에서 바로 완성합니다.")
    if not st.session_state.get("candidate"):
        st.info("먼저 '오늘 뭐 쓰지'에서 소재를 선택하세요."); return
    c=Candidate.model_validate(st.session_state.candidate)
    st.markdown(f"### {c.curiosity_hook}"); st.caption(f"{c.category} · 추천 {c.suggested_goal} · {c.asset_role}")
    goal=st.radio("이번 글의 목적",GOALS,index=GOALS.index(c.suggested_goal),horizontal=True,key="compose_goal")
    exp=st.text_area("내 경험·관찰 한 줄 (선택)",placeholder="예: 복지관에서 실제로 자주 봤던 장면",key="compose_exp")
    mode=mode_selector("compose_mode")
    if mode.startswith("🆓"):
        prompt=free_threads_prompt(c.topic,c.category,goal,korea_today().isoformat(),c.angle,c.conversation_trigger,exp,st.session_state.get("current_issue",""),st.session_state.get("issue_url",""),c.sensitivity)
        show_free_prompt("Threads 완성 프롬프트",prompt)
        st.markdown("**무료 후킹 뼈대**")
        for h in free_hook_suggestions(c.topic,c.category,goal): st.write("• "+h)
        if api_ready() and st.button("⚡ 이번 글만 앱에서 자동 완성 (API 사용)",key="compose_paid_once"):
            try:
                with st.spinner("한 번만 자동 완성 중…"):
                    d=parse_model(ThreadDraft,draft_prompt(c.topic,c.category,goal,c.angle,c.why_now,st.session_state.get("research",""),st.session_state.get("sources",[]),c.sensitivity,exp),selected_model()); count_api(1)
                load_draft(d); st.rerun()
            except Exception as e: st.error(f"원고 생성 오류: {e}")
    else:
        if st.button("✨ 앱에서 Threads 원고 완성",type="primary",key="compose_make"):
            if not api_ready(): st.error("API Key가 필요합니다. 무료모드로 전환하면 바로 사용할 수 있습니다.")
            else:
                try:
                    with st.spinner("첫줄·본문·질문·첫 댓글까지 편집 중…"):
                        d=parse_model(ThreadDraft,draft_prompt(c.topic,c.category,goal,c.angle,c.why_now,st.session_state.get("research",""),st.session_state.get("sources",[]),c.sensitivity,exp),selected_model()); count_api(1)
                    load_draft(d); st.rerun()
                except Exception as e: st.error(f"원고 생성 오류: {e}")

# ---------- QUICK ----------
def render_quick():
    page_header("✍️ 30초 글 만들기","무료모드는 한 줄 입력 → 완성 프롬프트 복사로 끝납니다.")
    mode=mode_selector("quick_mode")
    topic=st.text_input("무슨 얘기 할까요?",placeholder="예: X세대 여름휴가 / 부모님 혈압계 / 신당동 이름",key="quick_topic_input")
    cat=st.selectbox("카테고리",CATEGORIES,index=CATEGORIES.index(st.session_state.get("quick_category","오늘의 기억")),key="quick_cat")
    goal=st.radio("목적",["댓글형","궁금증형","정보형","공감형","저장형","수익형"],horizontal=True,key="quick_goal")
    exp=st.text_input("내 한마디 (선택)",placeholder="예: 나는 이걸 90년대에 직접 겪었다",key="quick_exp")
    if mode.startswith("🆓"):
        if not topic:
            st.caption("주제를 비우면 아래 버튼으로 오늘의 무료 추천 하나를 가져옵니다.")
            if st.button("🎲 오늘 주제 하나 골라줘",key="quick_pick"):
                b=free_candidate_board(korea_today().isoformat(),[cat],"균형 편집판","",1)
                st.session_state.quick_suggest=b.candidates[0].topic; st.rerun()
            if st.session_state.get("quick_suggest"): st.info("추천: "+st.session_state.quick_suggest)
        actual=topic or st.session_state.get("quick_suggest","")
        if actual:
            prompt=free_threads_prompt(actual,cat,goal,korea_today().isoformat(),experience_note=exp)
            show_free_prompt("30초 Threads 프롬프트",prompt)
    else:
        use_web=st.toggle("사실을 웹에서 확인 (비용 증가)",False,key="quick_web")
        if st.button("⚡ 바로 만들기",type="primary",key="quick_make"):
            if not api_ready(): st.error("API Key가 필요합니다.")
            else:
                try:
                    target=korea_today().isoformat(); research=""; sources=[]
                    actual=topic or free_candidate_board(target,[cat],"균형 편집판","",1).candidates[0].topic
                    with st.spinner("절약형 편집 중…"):
                        if use_web:
                            research,sources=web_research(quick_research_prompt(target,actual,cat),cheap_model()); count_api(1)
                        d=parse_model(ThreadDraft,draft_prompt(actual,cat,goal,"짧고 선명한 생활교양 각도",f"{target}에 읽기 좋은 소재",research,sources,"보통",exp),selected_model()); count_api(1)
                    st.session_state.research=research; st.session_state.sources=sources; st.session_state.candidate=None; load_draft(d); st.rerun()
                except Exception as e: st.error(f"생성 오류: {e}")

# ---------- WRITER ----------
def render_writer():
    page_header("📝 Threads 제작실","자동 완성된 글도 마지막 편집자는 사람입니다.")
    if not st.session_state.get("draft"):
        st.info("아직 자동 원고가 없습니다. 무료모드는 ChatGPT용 프롬프트를 복사해 사용합니다."); return
    d=ThreadDraft.model_validate(st.session_state.draft)
    st.markdown(f'<span class="pill blue">{d.category}</span><span class="pill coral">{d.goal}</span><span class="pill">민감도 {d.sensitivity}</span>',unsafe_allow_html=True)
    hook_candidate=st.selectbox("후킹 후보",d.hooks,key="writer_hook_candidate")
    if st.button("이 후킹을 첫줄에 적용",key="apply_hook",use_container_width=True): st.session_state.writer_hook_edit=hook_candidate; st.rerun()
    st.session_state.final_hook=st.text_input("첫줄 — 직접 수정",key="writer_hook_edit")
    st.session_state.final_body=st.text_area("본문 — 직접 수정",height=220,key="writer_body_edit")
    st.session_state.final_closing=st.text_input("마무리",key="writer_closing_edit")
    q_candidate=st.selectbox("질문 후보",["질문 없이 끝내기"]+d.discussion_questions,key="writer_q_candidate")
    if st.button("이 질문을 적용",key="apply_q",use_container_width=True):
        st.session_state.writer_question_edit="" if q_candidate=="질문 없이 끝내기" else q_candidate; st.rerun()
    st.session_state.final_question=st.text_input("댓글을 여는 질문 — 억지면 비우기",key="writer_question_edit")
    st.session_state.affiliate_on=st.checkbox("제휴 고지문 포함",value=st.session_state.get("affiliate_on",False),key="writer_aff")
    final=current_final_text(); st.markdown(f"**📋 최종 복사용 · {len(final)}자**"); st.code(final,language=None)
    st.link_button("Threads 열기 ↗","https://www.threads.com/",use_container_width=True)
    if d.topic_tag: st.info(f"🏷️ 추천 Topic: **{d.topic_tag}**")
    with st.expander("💬 첫 댓글 후보",expanded=True):
        for x in d.first_reply_options: st.code(x,language=None)
        if d.source_reply: st.code(d.source_reply,language=None)
    with st.expander("🔎 발행 전 사실검수"):
        for x in d.fact_check_points: st.write("- "+x)
        source_markdown(st.session_state.get("sources",[]))
    st.markdown("**선택형 유료 다듬기**")
    actions=["댓글 잘 달리게","더 궁금하게","더 재치 있게","더 전문적으로","더 짧게","더 따뜻하게"]
    cols=st.columns(2)
    for i,action in enumerate(actions):
        if cols[i%2].button(action,key=f"rw_{i}"):
            if not api_ready(): st.error("API Key가 필요합니다.")
            else:
                try:
                    r=parse_model(RewriteResult,rewrite_prompt(final,d.topic,d.category,d.goal,action,d.sensitivity),cheap_model()); count_api(1)
                    st.session_state.writer_hook_edit=r.hook; st.session_state.writer_body_edit=r.body; st.session_state.writer_closing_edit=r.closing_line; st.session_state.writer_question_edit=r.question; st.rerun()
                except Exception as e: st.error(str(e))
    a,b=st.columns(2)
    if a.button("🧪 AI 품질진단",key="quality"):
        if not api_ready(): st.error("API Key가 필요합니다.")
        else:
            try:
                qr=parse_model(QualityReview,review_prompt(final,d.topic,d.category,d.goal,d.sensitivity),cheap_model()); count_api(1); st.session_state.quality=qr.model_dump()
            except Exception as e: st.error(str(e))
    if b.button("💾 발행 후보 저장",key="save_post"):
        try:
            pid=save_post({"target_date":korea_today().isoformat(),"topic":d.topic,"category":d.category,"goal":d.goal,"selected_hook":st.session_state.final_hook,"final_text":final,"source_count":len(st.session_state.get("sources",[])),"status":"ready"}); st.session_state.last_saved_id=pid; st.success("저장했습니다.")
        except Exception as e: st.error(str(e))
    if st.session_state.get("quality"):
        qr=QualityReview.model_validate(st.session_state.quality)
        with st.expander("🧪 품질진단",expanded=True):
            sc=qr.scores; x,y,z=st.columns(3); x.metric("HOOK",sc.hook); y.metric("궁금증",sc.curiosity); z.metric("댓글성",sc.conversation)
            st.write("수정: "+" · ".join(qr.fixes)); st.caption(f"낚시 위험 {qr.clickbait_risk}/100")

# ---------- TALK ----------
def render_talk():
    page_header("💬 대화실","기본은 무료 프롬프트. 필요할 때만 자동 답글을 씁니다.")
    mode=mode_selector("talk_mode_select")
    kind=st.radio("무슨 답글인가요?",["내 글 댓글 답장","다른 글에 댓글 달기"],horizontal=True,key="talk_kind")
    source=st.text_area("원글 또는 맥락",placeholder="내 글 또는 상대방 글",height=110,key="talk_source")
    comment=st.text_area("답하고 싶은 댓글/내용",height=90,key="talk_comment")
    note=st.text_input("내가 꼭 넣고 싶은 말 (선택)",key="talk_note")
    if source or comment:
        if mode.startswith("🆓"):
            show_free_prompt("댓글 답장 프롬프트",free_reply_prompt(kind,source,comment,note))
        elif st.button("💬 답글 3안 자동 생성",type="primary",key="talk_make"):
            if not api_ready(): st.error("API Key가 필요합니다.")
            else:
                try:
                    rb=parse_model(ReplyBundle,reply_prompt(kind,source,comment,note),cheap_model()); count_api(1); st.session_state.reply_bundle=rb.model_dump()
                except Exception as e: st.error(str(e))
    if st.session_state.get("reply_bundle") and not mode.startswith("🆓"):
        rb=ReplyBundle.model_validate(st.session_state.reply_bundle)
        for opt in rb.options:
            with st.container(border=True): st.markdown(f"**{opt.label}**"); st.code(opt.text,language=None)

# ---------- MONEY ----------
def render_money():
    page_header("💰 돈 되는 소재 탐지기","무료 휴리스틱으로 먼저 판단하고, 깊이 분석만 선택적으로 API를 씁니다.")
    candidates=CandidateBoard.model_validate(st.session_state.board).candidates if st.session_state.get("board") else []
    if candidates:
        idx=st.selectbox("오늘 후보",range(len(candidates)),format_func=lambda i:f"{candidates[i].topic} · 💰{candidates[i].monetization_score}",key="money_candidate")
        c=candidates[idx]; topic=c.topic; cat=c.category; ss=c.search_asset_score; ms=c.monetization_score; risk=c.fact_risk; why=c.why_now
    else:
        topic=st.text_input("분석할 소재",placeholder="예: 부모님 혈압계 고르는 법",key="money_topic"); cat=st.selectbox("카테고리",CATEGORIES,key="money_cat"); ss=50; ms=50; risk=30; why="직접 입력"
    if topic:
        fm=free_money_map(topic,cat,ss,ms,risk)
        a,b=st.columns(2); a.metric("수익 연결",fm["money_score"]); b.metric("독자가치",fm["audience_value_score"])
        st.success("무료 추천 경로: "+fm["best_route"])
        for name,score,desc in fm["routes"]:
            st.progress(score/100,text=f"{name} · {score} — {desc}")
        st.warning(fm["warning"]); st.info("다음 자산: "+fm["next_asset"])
        if api_ready() and st.button("⚡ 수익경로 깊이 분석 (API)",key="money_paid"):
            try:
                mp=parse_model(MoneyPlan,money_prompt(topic,cat,why,ss,ms,risk),cheap_model()); count_api(1); st.session_state.money_plan=mp.model_dump(); st.rerun()
            except Exception as e: st.error(str(e))
    if st.session_state.get("money_plan"):
        mp=MoneyPlan.model_validate(st.session_state.money_plan)
        with st.expander("AI 깊이 분석",expanded=True):
            st.write(mp.one_line_strategy)
            for r in sorted(mp.routes,key=lambda x:x.fit_score,reverse=True): st.write(f"**{r.route} {r.fit_score}** · {r.why}")

# ---------- METRICS ----------
def render_metrics():
    page_header("📊 성과 학습","조회보다 답글·팔로우·클릭까지 같이 봅니다. 이 기능은 무료입니다.")
    try: p=posts_df()
    except Exception as e: st.error(f"저장소 오류: {e}"); return
    st.caption("현재 저장소: "+backend_name())
    if p.empty: st.info("자동 제작실에서 저장한 글이 아직 없습니다. 무료 글은 필요하면 수동 기록 기능을 다음 버전에 붙일 수 있습니다."); return
    ids=p["id"].astype(str).tolist(); pid=st.selectbox("성과 입력할 글",ids,format_func=lambda x:f"{p[p.id.astype(str)==x].iloc[0].topic}",key="metric_pid")
    a,b,c=st.columns(3); views=a.number_input("조회",0,step=100,key="m_views"); replies=b.number_input("답글",0,key="m_replies"); likes=c.number_input("좋아요",0,key="m_likes")
    a,b,c=st.columns(3); reposts=a.number_input("재게시",0,key="m_reposts"); follows=b.number_input("팔로우+",0,key="m_follows"); clicks=c.number_input("링크 클릭",0,key="m_clicks")
    orders=st.number_input("구매",0,key="m_orders"); rev=st.number_input("수익(원)",0.0,step=1000.0,key="m_rev")
    if st.button("📥 성과 저장",type="primary",key="metric_save"):
        from storage import save_metrics
        save_metrics(pid,views=views,likes=likes,replies=replies,reposts=reposts,follows=follows,link_clicks=clicks,orders=orders,revenue=rev); st.success("저장했습니다.")
    try:
        df=performance_df()
        if not df.empty:
            show=df.copy(); show["답글률%"]=(show["replies"]/show["views"].clip(lower=1)*100).round(2); show["클릭률%"]=(show["link_clicks"]/show["views"].clip(lower=1)*100).round(2)
            st.dataframe(show[[c for c in ["topic","category","goal","views","답글률%","클릭률%","orders","revenue"] if c in show.columns]],hide_index=True,use_container_width=True)
    except Exception as e: st.caption(str(e))

# ---------- EXPAND ----------
def render_expand():
    page_header("🔁 반응 좋은 글 확장","네이버·AdSense·Shorts 확장도 무료 프롬프트가 기본입니다.")
    mode=mode_selector("expand_mode")
    if st.session_state.get("draft"):
        d=ThreadDraft.model_validate(st.session_state.draft); topic=d.topic; final=current_final_text(); st.info("현재 자동 원고: "+topic)
    else:
        topic=st.text_input("확장할 주제",key="exp_topic"); final=st.text_area("Threads 원고",height=160,key="exp_text")
    channels=st.multiselect("확장 채널",["naver_blog","adsense_blog","youtube_shorts","instagram"],default=["naver_blog","youtube_shorts"],key="exp_channels")
    note=st.text_input("내 경험·사진·관찰",key="exp_note")
    if topic and final and channels:
        if mode.startswith("🆓"):
            show_free_prompt("멀티채널 확장 프롬프트",free_expand_prompt(topic,final,channels,note))
        elif st.button("🚀 플랫폼별 자동 재편집",type="primary",key="exp_make"):
            if not api_ready(): st.error("API Key가 필요합니다.")
            else:
                try:
                    bun=parse_model(MultiChannelBundle,platform_prompt(topic,final,channels,note),selected_model()); count_api(1); st.session_state.bundle=bun.model_dump()
                except Exception as e: st.error(str(e))
    if st.session_state.get("bundle") and not mode.startswith("🆓"):
        bun=MultiChannelBundle.model_validate(st.session_state.bundle)
        for d in bun.drafts:
            with st.expander(d.channel,expanded=True): st.selectbox("제목",d.title_options,key=f"t_{d.channel}"); st.text_area("원고",d.content,height=240,key=f"c_{d.channel}")

# ---------- OMNICHANNEL STUDIO ----------
def render_studio():
    page_header("✨ 한 소재로 5채널 + 이미지","복잡한 메뉴 대신 ① 주제 ② 톤 ③ 복사·편집의 세 단계로 끝냅니다.")
    cand=Candidate.model_validate(st.session_state.omni_candidate) if st.session_state.get("omni_candidate") else None
    default_topic=st.session_state.get("omni_topic") or (cand.topic if cand else "")

    st.markdown('<div class="dna-box"><b>오늘도 한살 DNA</b><br>더불어 사는 삶 · 민주주의와 평등 · 나보다 우리 · 모든 사람과 모든 일의 가치 · 낮은 곳으로 임하기.<br><b>글의 리듬:</b> 궁금증으로 열기 → 쉬운 정보로 약속 갚기 → 관찰형 재치 한 꼬집 → 독자가 자기 기억/경험을 말할 자리 → 사람 쪽의 여운.</div>',unsafe_allow_html=True)

    st.markdown("### 1. 소재와 결만 정하기")
    topic=st.text_input("오늘의 핵심 주제",value=default_topic,placeholder="예: 어떤 노래는 왜 첫 소절만으로 한 시절을 데려올까",key="omni_topic_input")
    default_cat=st.session_state.get("omni_category") or (cand.category if cand else "오늘의 기억")
    cat=st.selectbox("카테고리",CATEGORIES,index=CATEGORIES.index(default_cat) if default_cat in CATEGORIES else 0,key="omni_cat")

    editorial_modes=["설명형 에디토리얼","그리움+궁금증","생활교양 위트","사람·사회·공공","쓸모형"]
    visual_modes=["설명+그리움 하이브리드","에디토리얼 explainer","노스탤지어 콜라주","미니멀 인포그래픽"]
    c1,c2=st.columns(2)
    with c1:
        editorial=st.selectbox("글의 결",editorial_modes,index=editorial_modes.index(st.session_state.get("editorial_mode","설명형 에디토리얼")),key="omni_editorial")
    with c2:
        visual=st.selectbox("이미지 결",visual_modes,index=visual_modes.index(st.session_state.get("visual_mode","설명+그리움 하이브리드")),key="omni_visual")
    st.session_state.editorial_mode=editorial; st.session_state.visual_mode=visual

    generation=st.radio("세대 감성",["세대 연결형","조금 더 젊게","조금 더 그리운 쪽"],horizontal=True,key="omni_generation")
    st.session_state.generation_bridge=generation
    purpose=st.radio("이번 콘텐츠의 1차 역할",["사람 모으기","신뢰 쌓기","검색자산","수익 연결","브랜드 세계관"],horizontal=True,key="omni_purpose")
    experience=st.text_input("내 경험·관찰 한 줄 (선택)",placeholder="예: 90년대 노래를 들으면 몇 학년이었는지 바로 떠오른다",key="omni_exp")

    with st.expander("오늘 이슈/기사 연결 · 필요할 때만"):
        issue=st.text_input("이슈 한 줄",placeholder="없으면 비워두세요",key="omni_issue")
        url=st.text_input("참고 URL",placeholder="https://...",key="omni_url")

    channels=st.multiselect("만들 채널",OMNI_CHANNELS,default=OMNI_CHANNELS,key="omni_channels")
    money_intent=st.radio("수익 연결",["일단 정보와 신뢰","가능하면 자연스럽게","상품/제휴도 검토"],horizontal=True,key="omni_money")

    st.markdown('<div class="visual-box"><b>비주얼 원칙</b> · 현대 설명형 미디어의 대담한 정보 위계와 콜라주 감각은 참고하되 특정 매체의 레이아웃을 복제하지 않습니다. MORROWAY 고유의 크림·딥네이비·청록·코랄, 낡은 생활물건·거리·종이 질감·간결한 도형으로 “무슨 이야기지?”와 “아, 그때…”가 동시에 오게 만듭니다.</div>',unsafe_allow_html=True)

    mode=mode_selector("omni_mode")
    if topic and channels:
        prompt=omnichannel_free_prompt(
            topic,cat,purpose,korea_today().isoformat(),experience,issue,url,channels,money_intent,
            editorial_mode=editorial,visual_mode=visual,generation_bridge=generation
        )
        st.markdown("### 2. 한 번 복사 → ChatGPT")
        if mode.startswith("🆓"):
            st.markdown('<div class="copy-hint"><b>가장 쉬운 사용법</b> · 아래 프롬프트를 한 번 복사 → ChatGPT에 붙여넣기 → 나온 답변 전체를 다시 이 앱에 한 번 붙여넣기. API 비용은 0원입니다. ChatGPT 로그인은 보안상 앱이 대신할 수 없지만 Safari/앱에 로그인돼 있으면 세션은 유지됩니다.</div>',unsafe_allow_html=True)
            st.code(prompt,language=None)
            st.link_button("ChatGPT 열기 ↗ · 붙여넣기만 하세요","https://chatgpt.com/",use_container_width=True)
        else:
            use_web=st.toggle("최신·의학·역사 웹검증 (비용 증가)",False,key="omni_web")
            if st.button("⚡ 앱 안에서 콘텐츠팩 자동 생성",type="primary",key="omni_auto"):
                if not api_ready(): st.error("API Key가 필요합니다. 무료모드는 키 없이 사용 가능합니다.")
                else:
                    try:
                        final_prompt=prompt
                        if use_web:
                            research,sources=web_research(quick_research_prompt(korea_today().isoformat(),topic,cat),cheap_model()); count_api(1)
                            final_prompt += "\n\n[사실조사 메모]\n"+research
                            st.session_state.sources=sources
                        with st.spinner("플랫폼별 원고와 이미지 콘셉트를 편집 중…"):
                            raw=call_text(final_prompt,selected_model()); count_api(1)
                        st.session_state.omni_raw=raw; st.session_state.omni_sections=parse_omni_pack(raw); st.rerun()
                    except Exception as e: st.error(f"자동 생성 오류: {e}")

        st.markdown("### 3. 결과 전체를 한 번 붙여넣기")
        raw_input=st.text_area("ChatGPT 답변 전체",value=st.session_state.get("omni_raw",""),height=170,key="omni_raw_input",placeholder="ChatGPT 답변을 통째로 붙여넣으세요")
        if st.button("✂️ 자동 분리 → 편집 화면 열기",key="omni_parse",use_container_width=True):
            sections=parse_omni_pack(raw_input)
            if not sections: st.error("<<<THREADS>>> 같은 마커가 보이지 않습니다. ChatGPT 답변 전체를 그대로 붙여넣어 주세요.")
            else:
                st.session_state.omni_raw=raw_input; st.session_state.omni_sections=sections; st.success(f"{len(sections)}개 영역으로 정리했습니다."); st.rerun()

    sections=st.session_state.get("omni_sections",{})
    if sections:
        st.markdown("### 4. 필요한 것만 고쳐서 복사")
        social_tab, search_tab, visual_tab = st.tabs(["🧵 소셜","🔎 검색자산","🖼 이미지·가치"])
        edited={}

        def edit_block(key,label,height=150):
            if key not in sections: return
            st.markdown(f"**{label}**")
            val=st.text_area(label,value=sections.get(key,""),height=height,key=f"v15_edit_{key}",label_visibility="collapsed")
            edited[key]=val
            st.code(val,language=None)

        with social_tab:
            edit_block("THREADS","Threads",170)
            edit_block("FIRST_REPLY","첫 댓글",110)
            edit_block("SHORTS","YouTube Shorts 대본",190)
            edit_block("SHORTS_SHOTS","Shorts 장면·자막",170)
            edit_block("INSTAGRAM","Instagram",210)
        with search_tab:
            edit_block("NAVER","Naver Blog",250)
            edit_block("GOOGLE","Google Blog",250)
        with visual_tab:
            edit_block("EDITOR_NOTE","편집장 메모",120)
            edit_block("VALUE_CHECK","사람우선 가치점검",150)
            edit_block("IMAGE_1X1","1:1 이미지 프롬프트",170)
            if "IMAGE_1X1" in sections: st.link_button("1:1 이미지를 ChatGPT에서 만들기 ↗","https://chatgpt.com/",use_container_width=True)
            edit_block("IMAGE_9X16","9:16 이미지 프롬프트",170)
            edit_block("IMAGE_BLOG","블로그 대표 이미지 프롬프트",170)
            edit_block("MONEY_ROUTE","수익경로",130)
            edit_block("FACT_CHECK","팩트체크",150)

        st.session_state.omni_sections.update(edited)
        pack=omni_pack_to_text(st.session_state.omni_sections)
        st.download_button("📦 전체 콘텐츠팩 TXT 저장",pack.encode("utf-8-sig"),f"morroway_{korea_today().isoformat()}_content_pack.txt","text/plain",use_container_width=True)
        st.info("운영 원칙: Threads/Shorts/Instagram으로 먼저 대화와 반응을 확인하고, 반응 좋은 소재만 Naver/Google 장문으로 키웁니다. 수익은 그 다음입니다.")

# ---------- SETTINGS ----------
def render_settings():
    page_header("⚙️ 설정 & TOP100 LAB","장기 운영을 위해 무료 + 사람우선 + 멀티채널을 기본값으로 두었습니다.")
    st.markdown("### 비용 정책")
    st.success("🆓 무료 편집실 = API 크레딧 0원")
    st.info("⚡ AI 자동 = OpenAI API 사용량에 따라 비용 발생. 웹검색은 필요한 글에만 켜는 것을 권장합니다.")
    st.session_state.work_mode=st.radio("앱 기본 모드",["🆓 무료 편집","⚡ AI 자동"],index=0 if is_free() else 1,horizontal=True,key="set_work_mode")
    st.session_state.model_mode=st.radio("자동모드 모델",list(MODEL_MODES),index=list(MODEL_MODES).index(st.session_state.model_mode),horizontal=True,key="set_model")
    st.caption(f"현재 자동모델: {selected_model()} · 기본 추천은 절약(Luna)")
    if api_ready(): st.success("API Key 연결됨. 무료모드에서는 이 키를 사용하지 않습니다.")
    else: st.info("API Key 없음. 무료모드는 문제없이 사용 가능합니다.")
    st.metric("이번 세션 API 호출",st.session_state.api_calls)

    st.markdown("### MORROWAY DNA 기본값")
    st.caption("가치관을 구호처럼 반복하지 않고, 어떤 소재를 고르고 누구의 목소리를 놓치지 않는지에 반영합니다.")
    st.session_state.editorial_mode=st.selectbox("기본 글의 결",["설명형 에디토리얼","그리움+궁금증","생활교양 위트","사람·사회·공공","쓸모형"],index=["설명형 에디토리얼","그리움+궁금증","생활교양 위트","사람·사회·공공","쓸모형"].index(st.session_state.get("editorial_mode","설명형 에디토리얼")),key="set_editorial")
    st.session_state.visual_mode=st.selectbox("기본 이미지 결",["설명+그리움 하이브리드","에디토리얼 explainer","노스탤지어 콜라주","미니멀 인포그래픽"],index=["설명+그리움 하이브리드","에디토리얼 explainer","노스탤지어 콜라주","미니멀 인포그래픽"].index(st.session_state.get("visual_mode","설명+그리움 하이브리드")),key="set_visual")
    st.markdown('<div class="dna-box"><b>고정 편집가치</b> · 존엄 · 민주적 대화 · 평등 · 공동체 · 나보다 우리 · 낮은 곳의 시선 · 일하는 사람과 평범한 일상의 가치.<br>정치·역사처럼 관점이 갈리는 주제는 사실/해석/의견을 구분하고 정당한 이견을 왜곡하지 않습니다.</div>',unsafe_allow_html=True)

    st.markdown("### 🏆 TOP100 LAB")
    st.caption("공식 글로벌 Top100이 아니라 사용자가 모은 공개 우수글에서 '문법'만 추상화합니다. 이 분석 버튼만 API를 사용합니다.")
    sample="text,likes,replies,reposts,views,url,author\n샘플 게시물 문장,120,20,5,10000,,\n".encode("utf-8-sig")
    st.download_button("샘플 CSV",sample,"top100_import_sample.csv","text/csv")
    up=st.file_uploader("CSV / TSV / JSON",type=["csv","tsv","json"],key="topup")
    if up:
        try:
            df=read_benchmark_upload(up); st.dataframe(df.head(15),hide_index=True,use_container_width=True)
            if st.button("🧬 성공 문법 분석 (API 사용)",key="top_analyze"):
                if not api_ready(): st.error("API Key가 필요합니다.")
                else:
                    ta=parse_model(Top100Analysis,top100_prompt(benchmark_prompt_payload(df),len(df)),cheap_model()); count_api(1); save_style_profile(ta.model_dump()); st.session_state.top_profile=ta.model_dump(); st.success("문법 프로필 저장 완료")
        except Exception as e: st.error(str(e))
    profile=st.session_state.get("top_profile") or load_style_profile()
    if profile:
        ta=Top100Analysis.model_validate(profile); st.success(f"스타일 프로필 적용 · {ta.sample_size}개")

    st.markdown("### 데이터")
    try:
        p,m=export_all(); st.download_button("발행 기록 CSV",p.to_csv(index=False).encode("utf-8-sig"),"morroway_posts.csv","text/csv"); st.download_button("성과 기록 CSV",m.to_csv(index=False).encode("utf-8-sig"),"morroway_metrics.csv","text/csv")
    except Exception as e: st.caption(str(e))
    st.caption(APP_VERSION)

# ---------- router ----------
page=st.session_state.page
if page=="home": render_home()
elif page=="studio": render_studio()
elif page=="ideas": render_ideas()
elif page=="compose": render_compose()
elif page=="quick": render_quick()
elif page=="writer": render_writer()
elif page=="talk": render_talk()
elif page=="money": render_money()
elif page=="metrics": render_metrics()
elif page=="expand": render_expand()
elif page=="settings": render_settings()
else: go("home"); st.rerun()
