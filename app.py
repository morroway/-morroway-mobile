from __future__ import annotations
import os, json
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from engine import *
from models import *
from storage import save_post, save_metrics, posts_df, metrics_df, performance_df, backend_name, export_all
from top100_lab import read_benchmark_upload, benchmark_prompt_payload, save_style_profile, load_style_profile

load_dotenv()
ROOT=Path(__file__).parent
ASSET=ROOT/"morroway_home.png"
ICON=Image.open(ROOT/"morroway_icon.png")
APP_VERSION="MORROWAY MOBILE v1.2 beta"

st.set_page_config(page_title="오늘도 한살 편집국",page_icon=ICON,layout="centered",initial_sidebar_state="collapsed")

MOBILE_CSS="""
<style>
:root { --cream:#FAF6EC; --ink:#202322; --teal:#6F9FA1; --coral:#D96C4B; --olive:#41533B; --sand:#F0E9D9; }
html, body, [class*="css"] { font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif; }
.stApp { background: radial-gradient(circle at 50% 0%, #fffaf0 0%, var(--cream) 42%, #f7f1e3 100%); color:var(--ink); }
.block-container { max-width: 680px; padding-top: 0.8rem; padding-bottom: 6rem; padding-left: 1rem; padding-right:1rem; }
[data-testid="stHeader"] { background: rgba(250,246,236,.84); }
[data-testid="stSidebar"] { display:none; }
#MainMenu, footer { visibility:hidden; }
.hero-kicker { text-align:center; color:#6b6b64; font-size:.86rem; letter-spacing:.02em; margin-bottom:.55rem; }
.hero-title { text-align:center; font-size:1.05rem; font-weight:700; margin:.25rem 0 .1rem; }
.hero-sub { text-align:center; font-size:.92rem; color:#62635f; margin-bottom:1rem; }
.hero-logo img { border-radius:28px !important; box-shadow:0 14px 38px rgba(73,67,50,.12); border:1px solid rgba(111,159,161,.25); }
.stButton>button { width:100%; min-height:3.35rem; border-radius:17px; border:1px solid rgba(57,72,63,.15); font-weight:700; font-size:1rem; box-shadow:0 5px 14px rgba(70,60,45,.05); }
.stButton>button[kind="primary"] { background:var(--coral); border-color:var(--coral); color:white; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:20px; border-color:rgba(65,83,59,.15) !important; background:rgba(255,255,255,.55); }
[data-testid="stMetric"] { background:rgba(255,255,255,.62); padding:.65rem .7rem; border-radius:16px; border:1px solid rgba(65,83,59,.10); }
textarea, input { font-size:16px !important; }
.small-note { font-size:.82rem; color:#77756d; line-height:1.45; }
.pill { display:inline-block; margin:.12rem .22rem .12rem 0; padding:.26rem .52rem; border-radius:999px; background:#edf3ef; color:#425549; font-size:.77rem; font-weight:650; }
.pill.coral { background:#f8e2d9; color:#9c4b33; }
.pill.blue { background:#e1eeee; color:#436f73; }
.pill.gold { background:#f2e8c7; color:#745f20; }
.score-line { color:#62635f; font-size:.84rem; margin-top:.25rem; }
.brand-rule { border-top:1px solid rgba(111,159,161,.35); margin:1rem 0; }
.mobile-card-title { font-size:1.08rem; font-weight:800; line-height:1.4; margin-bottom:.35rem; }
.mobile-card-body { color:#55574f; line-height:1.55; font-size:.92rem; }
.section-title { font-size:1.32rem; font-weight:850; margin:.2rem 0 .2rem; }
.section-sub { color:#6b6c66; font-size:.9rem; margin-bottom:1rem; }
@media (max-width: 480px) {
  .block-container { padding-left:.78rem; padding-right:.78rem; padding-top:.35rem; }
  .stButton>button { min-height:3.55rem; font-size:.98rem; }
  [data-testid="stMetricValue"] { font-size:1.2rem; }
  .hero-logo img { border-radius:23px !important; }
}
</style>
"""
st.markdown(MOBILE_CSS,unsafe_allow_html=True)

# ---------- state ----------
def init_state():
    defaults={
        "page":"home","model_mode":"균형","board":None,"research":"","sources":[],
        "candidate":None,"draft":None,"final_hook":"","final_body":"","final_closing":"",
        "final_question":"","last_saved_id":None,"quick_topic":"","quick_category":"오늘의 기억",
    }
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v
init_state()

def go(page):
    st.session_state.page=page

def page_header(title,sub="",back=True):
    c1,c2=st.columns([1,5])
    if back and c1.button("←",key=f"back_{title}"): go("home"); st.rerun()
    with c2:
        st.markdown(f'<div class="section-title">{title}</div>',unsafe_allow_html=True)
        if sub: st.markdown(f'<div class="section-sub">{sub}</div>',unsafe_allow_html=True)

def api_ready(): return bool(get_api_key())

def selected_model(): return get_model(st.session_state.get("model_mode","균형"))

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
        d.topic_tag if d else "",
        st.session_state.get("affiliate_on",False),
    )

def load_draft(d:ThreadDraft):
    st.session_state.draft=d.model_dump()
    st.session_state.final_hook=d.hooks[0]
    st.session_state.final_body=d.body
    st.session_state.final_closing=d.closing_line
    st.session_state.final_question=d.discussion_questions[0] if d.discussion_questions else ""
    st.session_state.writer_hook_edit=d.hooks[0]
    st.session_state.writer_body_edit=d.body
    st.session_state.writer_closing_edit=d.closing_line
    st.session_state.writer_question_edit=d.discussion_questions[0] if d.discussion_questions else ""
    st.session_state.page="writer"

# ---------- HOME ----------
def render_home():
    today=korea_today()
    st.markdown(f'<div class="hero-kicker">{today.strftime("%Y.%m.%d")} · 오늘도 한살 편집국</div>',unsafe_allow_html=True)
    st.markdown('<div class="hero-logo">',unsafe_allow_html=True)
    st.image(str(ASSET),use_container_width=True)
    st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="hero-title">하루 한 스푼의 지혜를, 대화가 시작되는 글로.</div>',unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">이동 중에도 소재 찾기 → 글쓰기 → 질문 → 첫 댓글 → 복사까지.</div>',unsafe_allow_html=True)

    a,b=st.columns(2)
    if a.button("🔥 오늘 뭐 쓰지",type="primary",key="home_ideas"): go("ideas"); st.rerun()
    if b.button("✍️ 30초 글 만들기",key="home_quick"): go("quick"); st.rerun()
    c,d=st.columns(2)
    if c.button("💬 대화실",key="home_talk"): go("talk"); st.rerun()
    if d.button("💰 돈 되는 소재",key="home_money"): go("money"); st.rerun()

    st.markdown('<div class="brand-rule"></div>',unsafe_allow_html=True)
    st.caption("빠른 메뉴")
    e,f,g=st.columns(3)
    if e.button("📊 성과",key="home_metrics"): go("metrics"); st.rerun()
    if f.button("🔁 확장",key="home_expand"): go("expand"); st.rerun()
    if g.button("⚙️ 설정",key="home_settings"): go("settings"); st.rerun()

    if not api_ready():
        st.warning("AI 자동생성은 OpenAI API Key 설정 후 작동합니다. 설정에서 로컬 키를 넣거나, 클라우드 배포 시 Secrets에 한 번만 저장하세요.")
    else:
        st.success(f"AI 연결됨 · {st.session_state.model_mode} 모드")

    st.markdown("""
    <div class="small-note">Threads 최적화 원칙: 억지 질문보다 <b>답하기 쉬운 구체적 경험 질문</b>, 낚시보다 <b>첫줄의 정보 빈칸과 빠른 payoff</b>, 민감한 역사·질병·피해 주제에는 <b>위트보다 존엄과 정확성</b>을 우선합니다.</div>
    """,unsafe_allow_html=True)

# ---------- IDEAS ----------
def render_ideas():
    page_header("🔥 오늘 뭐 쓰지","계절·기념일·최근 이슈·역사·건강을 한 번에 편집회의합니다.")
    target=st.date_input("기준일",value=korea_today(),key="ideas_date").isoformat()
    pattern=st.selectbox("오늘의 편집판",list(JOURNAL_PATTERNS),index=1,key="ideas_pattern")
    cats=st.multiselect("관심 카테고리",CATEGORIES,default=CATEGORIES,key="ideas_cats")
    manual=st.text_input("오늘 특별히 보고 싶은 것",placeholder="예: 서울 지명, 90년대 직장문화, 부모님 여름 건강",key="ideas_manual")
    n=st.slider("후보 수",5,12,7,key="ideas_n")
    use_web=st.toggle("최신 웹 조사",True,key="ideas_web")
    if st.button("🗞️ 오늘의 추천 만들기",type="primary",key="make_board"):
        if not api_ready(): st.error("설정에서 OpenAI API Key를 먼저 연결해주세요.")
        elif not cats: st.error("카테고리를 하나 이상 골라주세요.")
        else:
            try:
                model=selected_model(); cal=calendar_context(target)
                with st.spinner("오늘의 편집회의 중…"):
                    if use_web:
                        research,sources=web_research(research_prompt(target,cats,JOURNAL_PATTERNS[pattern],manual,cal),model)
                    else:
                        research="웹검색 미사용. 내장 캘린더와 상시형 소재만 사용하고 최신 사실은 단정하지 않는다."; sources=[]
                    board=parse_model(CandidateBoard,board_prompt(target,cats,JOURNAL_PATTERNS[pattern],manual,research,sources,n),model)
                st.session_state.board=board.model_dump(); st.session_state.research=research; st.session_state.sources=sources
            except Exception as e: st.error(f"생성 오류: {e}")
    if st.session_state.get("board"):
        board=CandidateBoard.model_validate(st.session_state.board)
        st.info(board.editorial_note)
        for i,cand in enumerate(board.candidates,1):
            with st.container(border=True):
                st.markdown(f'<div class="mobile-card-title">{i}. {cand.curiosity_hook}</div>',unsafe_allow_html=True)
                st.markdown(f'<span class="pill blue">{cand.category}</span><span class="pill">{cand.asset_role}</span><span class="pill coral">추천 {cand.suggested_goal}</span>',unsafe_allow_html=True)
                st.markdown(f'<div class="mobile-card-body">{cand.why_now}<br><b>댓글 방아쇠:</b> {cand.conversation_trigger}</div>',unsafe_allow_html=True)
                st.markdown(f'<div class="score-line">👀 {cand.reach_score} · 💬 {cand.conversation_score} · ❓ {cand.curiosity_score} · 🔖 {cand.save_score} · 💰 {cand.monetization_score} · ⚠️ {cand.fact_risk}</div>',unsafe_allow_html=True)
                if st.button("이 소재로 글 만들기",key=f"pick_{i}",use_container_width=True):
                    st.session_state.candidate=cand.model_dump(); st.session_state.page="compose"; st.rerun()
        with st.expander("🔎 조사 메모와 출처"):
            st.write(st.session_state.research); source_markdown(st.session_state.sources)

# ---------- COMPOSE ----------
def render_compose():
    page_header("✍️ 글의 목적 고르기","같은 소재도 댓글형·궁금증형·정보형은 완전히 다르게 씁니다.")
    if not st.session_state.get("candidate"):
        st.info("먼저 '오늘 뭐 쓰지'에서 소재를 선택하세요."); return
    c=Candidate.model_validate(st.session_state.candidate)
    st.markdown(f"### {c.curiosity_hook}")
    st.caption(f"{c.category} · 추천 목적 {c.suggested_goal} · {c.asset_role}")
    goal=st.radio("이번 글의 목적",GOALS,index=GOALS.index(c.suggested_goal),horizontal=True,key="compose_goal")
    exp=st.text_area("내 경험·관찰 한 줄 (선택)",placeholder="예: 복지관에서 실제로 자주 봤던 장면 / 내가 느낀 점",key="compose_exp")
    if st.button("✨ Threads 원고 만들기",type="primary",key="compose_make"):
        if not api_ready(): st.error("OpenAI API Key가 필요합니다.")
        else:
            try:
                with st.spinner("첫줄·본문·질문·첫 댓글까지 편집 중…"):
                    d=parse_model(ThreadDraft,draft_prompt(c.topic,c.category,goal,c.angle,c.why_now,st.session_state.get("research",""),st.session_state.get("sources",[]),c.sensitivity,exp),selected_model())
                load_draft(d); st.rerun()
            except Exception as e: st.error(f"원고 생성 오류: {e}")

# ---------- QUICK ----------
def render_quick():
    page_header("✍️ 30초 글 만들기","소재 한 줄만 적고 바로 초안을 만듭니다.")
    topic=st.text_input("무슨 얘기 할까요?",value=st.session_state.get("quick_topic",""),placeholder="비워두면 오늘과 연결된 생활교양 소재를 AI가 고릅니다.",key="quick_topic_input")
    cat=st.selectbox("카테고리",CATEGORIES,index=CATEGORIES.index(st.session_state.get("quick_category","오늘의 기억")),key="quick_cat")
    goal=st.radio("목적",["댓글형","궁금증형","정보형","공감형","저장형","수익형"],horizontal=True,key="quick_goal")
    use_web=st.toggle("사실을 웹에서 확인",True,key="quick_web")
    exp=st.text_input("내 한마디 (선택)",placeholder="예: 나는 이걸 90년대에 직접 겪었다",key="quick_exp")
    if st.button("⚡ 바로 만들기",type="primary",key="quick_make"):
        if not api_ready(): st.error("OpenAI API Key가 필요합니다.")
        else:
            try:
                target=korea_today().isoformat(); research=""; sources=[]
                with st.spinner("30초 편집 중…"):
                    if use_web:
                        research,sources=web_research(quick_research_prompt(target,topic,cat),selected_model())
                    actual_topic=topic or f"{target} 오늘과 연결되는 {cat} 이야기 한 가지"
                    d=parse_model(ThreadDraft,draft_prompt(actual_topic,cat,goal,"짧고 선명한 생활교양 각도",f"{target}에 읽기 좋은 소재",research,sources,"보통",exp),selected_model())
                st.session_state.research=research; st.session_state.sources=sources; st.session_state.candidate=None
                load_draft(d); st.rerun()
            except Exception as e: st.error(f"생성 오류: {e}")

# ---------- WRITER ----------
def render_writer():
    page_header("📝 Threads 제작실","훅은 세게, 내용은 알차게, 질문은 자연스럽게.")
    if not st.session_state.get("draft"):
        st.info("아직 원고가 없습니다. 홈에서 30초 글 만들기 또는 오늘 뭐 쓰지를 시작하세요."); return
    d=ThreadDraft.model_validate(st.session_state.draft)
    st.markdown(f'<span class="pill blue">{d.category}</span><span class="pill coral">{d.goal}</span><span class="pill">민감도 {d.sensitivity}</span>',unsafe_allow_html=True)

    hook_candidate=st.selectbox("후킹 후보",d.hooks,key="writer_hook_candidate")
    if st.button("이 후킹을 첫줄에 적용",key="apply_hook",use_container_width=True):
        st.session_state.writer_hook_edit=hook_candidate; st.session_state.final_hook=hook_candidate; st.rerun()
    h=st.text_input("첫줄 — 직접 수정 가능",key="writer_hook_edit")
    st.session_state.final_hook=h

    if d.first_lines:
        with st.expander("첫줄 다음 문장 후보"):
            for x in d.first_lines: st.write("• "+x)
    b=st.text_area("본문 — 여기서 직접 수정",height=220,key="writer_body_edit")
    st.session_state.final_body=b
    cl=st.text_input("마무리",key="writer_closing_edit"); st.session_state.final_closing=cl

    q_candidate=st.selectbox("질문 후보",["질문 없이 끝내기"]+d.discussion_questions,key="writer_q_candidate")
    if st.button("이 질문을 적용",key="apply_q",use_container_width=True):
        qv="" if q_candidate=="질문 없이 끝내기" else q_candidate
        st.session_state.writer_question_edit=qv; st.session_state.final_question=qv; st.rerun()
    q=st.text_input("댓글을 여는 질문 — 억지면 비워두세요",key="writer_question_edit")
    st.session_state.final_question=q

    st.session_state.affiliate_on=st.checkbox("제휴 고지문 포함",value=st.session_state.get("affiliate_on",False),key="writer_aff")

    final=current_final_text()
    st.markdown(f"**📋 최종 복사용 · {len(final)}자**")
    st.code(final,language=None)
    st.caption("코드블록의 복사 아이콘을 누른 뒤 Threads로 이동하세요.")
    st.link_button("Threads 열기 ↗", "https://www.threads.com/", use_container_width=True)
    if len(final)>500: st.info("기본 게시물 500자를 넘습니다. 핵심을 줄이거나 연속 스레드/긴 텍스트 첨부를 고려하세요.")

    if d.topic_tag: st.info(f"🏷️ Threads 작성 화면 추천 Topic: **{d.topic_tag}**")
    if d.poll.suitable:
        with st.expander("📊 설문으로 바꿔도 좋은 소재"):
            st.write(d.poll.question); st.write(" / ".join(d.poll.options))

    with st.expander("💬 첫 댓글(자기 답글) 후보",expanded=True):
        for i,x in enumerate(d.first_reply_options,1): st.code(x,language=None)
        if d.source_reply: st.markdown("**출처/보충용**"); st.code(d.source_reply,language=None)

    with st.expander("🔎 발행 전 사실검수"):
        for x in d.fact_check_points: st.write("- "+x)
        source_markdown(st.session_state.get("sources",[]))

    st.markdown("**한 번 더 다듬기**")
    actions=["댓글 잘 달리게","더 궁금하게","더 재치 있게","더 전문적으로","더 짧게","더 따뜻하게"]
    for row in range(3):
        c1,c2=st.columns(2)
        for col,action in zip([c1,c2],actions[row*2:row*2+2]):
            if col.button(action,key=f"rw_{action}",use_container_width=True):
                try:
                    with st.spinner("다시 편집 중…"):
                        r=parse_model(RewriteResult,rewrite_prompt(final,d.topic,d.category,d.goal,action,d.sensitivity),selected_model())
                    st.session_state.final_hook=r.hook; st.session_state.final_body=r.body; st.session_state.final_closing=r.closing_line; st.session_state.final_question=r.question
                    st.session_state.writer_hook_edit=r.hook; st.session_state.writer_body_edit=r.body; st.session_state.writer_closing_edit=r.closing_line; st.session_state.writer_question_edit=r.question
                    st.session_state.rewrite_note=r.editor_note; st.rerun()
                except Exception as e: st.error(f"재작성 오류: {e}")
    if st.session_state.get("rewrite_note"): st.caption("편집 메모: "+st.session_state.rewrite_note)

    c1,c2=st.columns(2)
    if c1.button("🧪 품질 진단",key="quality",use_container_width=True):
        try:
            with st.spinner("궁금증·댓글성·전문성 진단 중…"):
                qr=parse_model(QualityReview,review_prompt(final,d.topic,d.category,d.goal,d.sensitivity),selected_model())
            st.session_state.quality=qr.model_dump()
        except Exception as e: st.error(f"진단 오류: {e}")
    if c2.button("💾 발행 후보 저장",key="save_post",use_container_width=True):
        try:
            pid=save_post({"target_date":korea_today().isoformat(),"topic":d.topic,"category":d.category,"goal":d.goal,"selected_hook":st.session_state.final_hook,"final_text":final,"source_count":len(st.session_state.get("sources",[])),"status":"ready"})
            st.session_state.last_saved_id=pid; st.success("발행 후보로 저장했습니다.")
        except Exception as e: st.error(f"저장 오류: {e}")
    if st.session_state.get("quality"):
        qr=QualityReview.model_validate(st.session_state.quality)
        with st.expander("🧪 편집장 품질진단",expanded=True):
            sc=qr.scores
            a,b,c=st.columns(3); a.metric("HOOK",sc.hook); b.metric("궁금증",sc.curiosity); c.metric("댓글성",sc.conversation)
            a,b,c=st.columns(3); a.metric("전문성",sc.expertise); b.metric("쓸모",sc.usefulness); c.metric("종합",sc.total)
            st.write("**강점** · "+" · ".join(qr.strengths)); st.write("**수정** · "+" · ".join(qr.fixes))
            st.caption(f"질문 자연스러움: {'예' if qr.question_is_natural else '아니오'} · 낚시 위험 {qr.clickbait_risk}/100")
            if st.button("진단 수정안 적용",key="apply_quality"):
                st.session_state.final_hook=qr.revised_hook; st.session_state.final_body=qr.revised_body; st.session_state.final_closing=qr.revised_closing; st.session_state.final_question=qr.revised_question
                st.session_state.writer_hook_edit=qr.revised_hook; st.session_state.writer_body_edit=qr.revised_body; st.session_state.writer_closing_edit=qr.revised_closing; st.session_state.writer_question_edit=qr.revised_question
                st.rerun()

# ---------- TALK ----------
def render_talk():
    page_header("💬 대화실","Threads는 글만큼 답글도 중요합니다. 빈말 대신 대화를 이어갑니다.")
    mode=st.radio("무슨 답글인가요?",["내 글 댓글 답장","다른 글에 댓글 달기"],horizontal=True,key="talk_mode")
    source=st.text_area("원글 또는 맥락",placeholder="내 글 또는 상대방 글을 붙여넣기",height=120,key="talk_source")
    comment=st.text_area("답하고 싶은 댓글/내용",placeholder="상대 댓글 또는 내가 반응할 문장",height=100,key="talk_comment")
    note=st.text_input("내가 꼭 넣고 싶은 한마디 (선택)",key="talk_note")
    if st.button("💬 답글 3안 만들기",type="primary",key="talk_make"):
        if not api_ready(): st.error("OpenAI API Key가 필요합니다.")
        elif not (source or comment): st.warning("원글이나 댓글을 붙여넣어주세요.")
        else:
            try:
                with st.spinner("사람 냄새 나는 답글을 만드는 중…"):
                    rb=parse_model(ReplyBundle,reply_prompt(mode,source,comment,note),selected_model())
                st.session_state.reply_bundle=rb.model_dump()
            except Exception as e: st.error(f"답글 생성 오류: {e}")
    if st.session_state.get("reply_bundle"):
        rb=ReplyBundle.model_validate(st.session_state.reply_bundle)
        st.caption(rb.context_summary)
        for opt in rb.options:
            with st.container(border=True):
                st.markdown(f"**{opt.label}**"); st.code(opt.text,language=None); st.caption(opt.why)
        if rb.avoid: st.warning("피하면 좋은 것: "+" · ".join(rb.avoid))

# ---------- MONEY ----------
def render_money():
    page_header("💰 돈 되는 소재 탐지기","모든 글을 팔려고 하지 않고, 어떤 수익 경로에 맞는지 구분합니다.")
    candidates=[]
    if st.session_state.get("board"):
        board=CandidateBoard.model_validate(st.session_state.board); candidates=board.candidates
    if candidates:
        labels=[f"{c.topic} · 💰{c.monetization_score} · 검색{c.search_asset_score}" for c in candidates]
        idx=st.selectbox("오늘 후보에서 선택",range(len(candidates)),format_func=lambda i:labels[i],key="money_candidate")
        c=candidates[idx]; topic=c.topic; cat=c.category; why=c.why_now; ss=c.search_asset_score; ms=c.monetization_score; risk=c.fact_risk
    else:
        topic=st.text_input("분석할 소재",placeholder="예: 부모님 혈압계 고르는 법",key="money_topic")
        cat=st.selectbox("카테고리",CATEGORIES,key="money_cat"); why="사용자 직접 입력 소재"; ss=50; ms=50; risk=30
    if st.button("🧭 수익 지도 만들기",type="primary",key="money_make"):
        if not topic: st.warning("소재를 입력하세요.")
        elif not api_ready(): st.error("OpenAI API Key가 필요합니다.")
        else:
            try:
                with st.spinner("제휴·검색·자체상품·쇼츠 경로를 나눠 보는 중…"):
                    mp=parse_model(MoneyPlan,money_prompt(topic,cat,why,ss,ms,risk),selected_model())
                st.session_state.money_plan=mp.model_dump()
            except Exception as e: st.error(f"분석 오류: {e}")
    if st.session_state.get("money_plan"):
        mp=MoneyPlan.model_validate(st.session_state.money_plan)
        a,b=st.columns(2); a.metric("MONEY",mp.money_score); b.metric("독자가치",mp.audience_value_score)
        st.success(mp.one_line_strategy); st.markdown(f"**최우선 경로:** {mp.best_route}")
        for r in sorted(mp.routes,key=lambda x:x.fit_score,reverse=True):
            with st.expander(f"{r.route} · 적합도 {r.fit_score}"):
                st.write(r.why); st.write("**아이디어:** "+r.offer_idea); st.write("**연결:** "+r.content_bridge); st.write("**시점:** "+r.timing)
        if mp.do_not_sell: st.warning("억지로 팔지 말 것: "+" · ".join(mp.do_not_sell))
        st.info("다음 자산: "+mp.next_asset)

# ---------- METRICS ----------
def render_metrics():
    page_header("📊 성과 학습","실제 조회·답글·팔로우·클릭을 기록하면 내 계정의 승리 패턴이 보입니다.")
    try: p=posts_df()
    except Exception as e: st.error(f"저장소 연결 오류: {e}"); return
    st.caption("현재 저장소: "+backend_name())
    if p.empty:
        st.info("아직 저장된 발행 후보가 없습니다. 제작실에서 먼저 저장하세요."); return
    ids=p["id"].astype(str).tolist()
    pid=st.selectbox("성과 입력할 글",ids,format_func=lambda x: f"{p[p.id.astype(str)==x].iloc[0].topic}",key="metric_pid")
    a,b,c=st.columns(3); views=a.number_input("조회",0,step=100,key="m_views"); replies=b.number_input("답글",0,key="m_replies"); likes=c.number_input("좋아요",0,key="m_likes")
    a,b,c=st.columns(3); reposts=a.number_input("재게시",0,key="m_reposts"); quotes=b.number_input("인용",0,key="m_quotes"); follows=c.number_input("팔로우+",0,key="m_follows")
    a,b,c=st.columns(3); pv=a.number_input("프로필 방문",0,key="m_pv"); clicks=b.number_input("링크 클릭",0,key="m_clicks"); orders=c.number_input("구매",0,key="m_orders")
    rev=st.number_input("수익(원)",0.0,step=1000.0,key="m_rev")
    if st.button("📥 성과 저장",type="primary",key="metric_save"):
        try:
            save_metrics(pid,views=views,likes=likes,replies=replies,reposts=reposts,quotes=quotes,profile_visits=pv,follows=follows,link_clicks=clicks,orders=orders,revenue=rev)
            st.success("저장했습니다.")
        except Exception as e: st.error(f"저장 오류: {e}")
    try:
        df=performance_df()
        if not df.empty:
            total_views=int(pd.to_numeric(df.get("views",0),errors="coerce").fillna(0).sum()); total_replies=int(pd.to_numeric(df.get("replies",0),errors="coerce").fillna(0).sum()); total_clicks=int(pd.to_numeric(df.get("link_clicks",0),errors="coerce").fillna(0).sum())
            a,b,c=st.columns(3); a.metric("누적 조회",f"{total_views:,}"); b.metric("답글",f"{total_replies:,}"); c.metric("클릭",f"{total_clicks:,}")
            show=df.copy()
            if "views" in show:
                show["답글률%"]=(show["replies"]/show["views"].clip(lower=1)*100).round(2); show["팔로우전환%"]=(show["follows"]/show["views"].clip(lower=1)*100).round(2); show["클릭률%"]=(show["link_clicks"]/show["views"].clip(lower=1)*100).round(2)
                st.dataframe(show[[c for c in ["topic","category","goal","views","답글률%","팔로우전환%","클릭률%","orders","revenue"] if c in show.columns]],hide_index=True,use_container_width=True)
    except Exception as e: st.caption(f"성과 요약을 불러오지 못했습니다: {e}")

# ---------- EXPAND ----------
def render_expand():
    page_header("🔁 반응 좋은 글 확장","Threads에서 검증된 소재만 네이버·AdSense·Shorts로 키웁니다.")
    if st.session_state.get("draft"):
        d=ThreadDraft.model_validate(st.session_state.draft); topic=d.topic; final=current_final_text()
        st.info("현재 제작실 원고를 확장합니다: "+topic)
    else:
        topic=st.text_input("확장할 주제",key="exp_topic"); final=st.text_area("Threads 원고",height=170,key="exp_text")
    channels=st.multiselect("확장 채널",["naver_blog","adsense_blog","youtube_shorts","instagram"],default=["naver_blog","youtube_shorts"],key="exp_channels")
    note=st.text_input("내 경험·사진·관찰 메모",key="exp_note")
    if st.button("🚀 플랫폼별 재편집",type="primary",key="exp_make"):
        if not topic or not final: st.warning("주제와 원고가 필요합니다.")
        elif not api_ready(): st.error("OpenAI API Key가 필요합니다.")
        else:
            try:
                with st.spinner("플랫폼 의도에 맞게 다시 쓰는 중…"):
                    bun=parse_model(MultiChannelBundle,platform_prompt(topic,final,channels,note),selected_model())
                st.session_state.bundle=bun.model_dump()
            except Exception as e: st.error(f"확장 오류: {e}")
    if st.session_state.get("bundle"):
        bun=MultiChannelBundle.model_validate(st.session_state.bundle)
        for d in bun.drafts:
            with st.expander(d.channel,expanded=True):
                title=st.selectbox("제목",d.title_options,key=f"expt_{d.channel}"); st.text_area("원고",d.content,height=280,key=f"expc_{d.channel}")
                st.write("검색어: "+" · ".join(d.search_keywords)); st.write("사람이 더할 것: "+" · ".join(d.human_value_add)); st.caption(d.monetization_note)

# ---------- SETTINGS / LAB ----------
def render_settings():
    page_header("⚙️ 설정 & 실험실","모바일에서는 API Key를 매번 넣지 않도록 클라우드 Secrets 사용을 권장합니다.")
    st.session_state.model_mode=st.radio("AI 모드",list(MODEL_MODES),index=list(MODEL_MODES).index(st.session_state.model_mode),horizontal=True,key="set_mode")
    st.caption(f"현재 모델: {selected_model()} · 절약=Luna / 균형=Terra / 고품질=Sol")
    try:
        cloud_key=bool(st.secrets.get("OPENAI_API_KEY"))
    except Exception:
        cloud_key=False
    if not cloud_key:
        key=st.text_input("로컬 테스트용 OpenAI API Key",value=st.session_state.get("runtime_api_key",""),type="password",key="set_key")
        if key: st.session_state.runtime_api_key=key
    else:
        st.success("OpenAI API Key가 Streamlit Secrets에 안전하게 연결되어 있습니다.")
    st.info("저장소: "+backend_name()+" · 모바일 클라우드에서 성과를 영구 보관하려면 Google Sheets 연결을 권장합니다.")

    st.markdown("### 🏆 TOP100 LAB")
    st.caption("Meta 공식 글로벌 Top100이 아니라, 사용자가 수집한 공개 우수글 최대 100개에서 문법만 추상화합니다. 원문은 복제하지 않습니다.")
    sample=(ROOT/"data"/"benchmarks"/"top100_import_sample.csv").read_bytes()
    st.download_button("샘플 CSV",sample,"top100_import_sample.csv","text/csv")
    up=st.file_uploader("CSV / TSV / JSON",type=["csv","tsv","json"],key="topup")
    if up:
        try:
            df=read_benchmark_upload(up); st.dataframe(df.head(20),hide_index=True,use_container_width=True)
            if st.button("🧬 성공 문법 분석",key="top_analyze"):
                if not api_ready(): st.error("API Key가 필요합니다.")
                else:
                    payload=benchmark_prompt_payload(df)
                    with st.spinner("원문을 버리고 구조만 추상화하는 중…"):
                        ta=parse_model(Top100Analysis,top100_prompt(payload,len(df)),selected_model())
                    save_style_profile(ta.model_dump()); st.session_state.top_profile=ta.model_dump(); st.success("새 글부터 스타일 프로필이 적용됩니다.")
        except Exception as e: st.error(f"TOP100 분석 오류: {e}")
    profile=st.session_state.get("top_profile") or load_style_profile()
    if profile:
        ta=Top100Analysis.model_validate(profile); st.success(f"벤치마크 프로필 적용 중 · {ta.sample_size}개")
        with st.expander("현재 문법 프로필"):
            st.write("**강한 신호:** "+" · ".join(ta.strongest_signals)); st.write("**리듬:** "+" · ".join(ta.rhythm_rules)); st.write("**대화:** "+" · ".join(ta.conversation_rules)); st.warning("피할 것: "+" · ".join(ta.anti_patterns))

    st.markdown("### 데이터 내보내기")
    try:
        p,m=export_all(); st.download_button("발행 기록 CSV",p.to_csv(index=False).encode("utf-8-sig"),"morroway_posts.csv","text/csv"); st.download_button("성과 기록 CSV",m.to_csv(index=False).encode("utf-8-sig"),"morroway_metrics.csv","text/csv")
    except Exception as e: st.caption(str(e))

    st.markdown("### 앱 원칙")
    st.write("• 댓글을 구걸하지 않고 답하기 쉬운 경험 질문을 만든다.\n\n• 첫줄이 만든 궁금증은 초반에 반드시 갚는다.\n\n• 건강·근현대사·정치·인권은 원자료 확인을 우선한다.\n\n• 수익은 독자가치 뒤에 둔다.\n\n• 민감한 피해·참사·죽음 주제에는 유머를 쓰지 않는다.")
    st.caption(APP_VERSION)

# ---------- router ----------
page=st.session_state.page
if page=="home": render_home()
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
