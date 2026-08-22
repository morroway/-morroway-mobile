from __future__ import annotations
import json, os, hashlib
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Type
from pydantic import BaseModel
from models import *
from top100_lab import style_profile_brief

ROOT=Path(__file__).parent
CAL_PATH=(ROOT/"editorial_calendar.json") if (ROOT/"editorial_calendar.json").exists() else (ROOT/"data"/"editorial_calendar.json")

CATEGORIES=[
    "오늘의 몸","오늘의 돌봄","오늘의 마음","오늘의 기억","오늘의 역사",
    "오늘의 동네","오늘의 취향","오늘의 쓸모","계절·기념일","오늘의 이슈"
]
GOALS=["댓글형","궁금증형","공감형","정보형","저장형","수익형","설문형","확장형"]
JOURNAL_PATTERNS={
    "균형 편집판":"건강·돌봄·역사·지명·추억·생활 쓸모를 고르게 섞는다.",
    "오늘 뭐 있지?":"기준일 계절·기념일·최근 이슈를 우선하되 억지로 연결하지 않는다.",
    "역사 탐정판":"지명 유래·근현대사·옛 사회상·사라진 생활문화·기억을 우선한다.",
    "몸과 돌봄판":"건강·약·식사·운동·부모 돌봄·노인복지를 우선한다.",
    "추억 소환판":"1970~2000년대 음악·물건·거리·학교·직장·방송·생활문화를 우선한다.",
    "쓸모와 수익판":"생활 문제 해결과 제품 선택 기준을 우선한다. 판매보다 판단 기준이 먼저다.",
}
MODEL_MODES={
    "절약":"gpt-5.6-luna",
    "균형":"gpt-5.6-terra",
    "고품질":"gpt-5.6",
}

THREADS_OFFICIAL_SIGNALS="""
Threads 운영에 반영할 편집 신호:
- 답글과 대화가 중요한 플랫폼이므로 일방적 방송보다 자기 경험을 말하기 쉬운 글을 우선한다.
- 유머는 가벼운 생활·추억 소재에서 관찰형으로만 쓰고 피해·참사·질병·죽음·인권 침해에는 쓰지 않는다.
- Threads 전용 원고를 만든다. 타 플랫폼 문장을 그대로 복사하지 않는다.
- topic은 한 게시물에 가장 맞는 하나만 제안한다.
- 억지 댓글 유도, 분노 유도, 거짓 낚시, '댓글 남겨주세요/팔로우해주세요' 같은 engagement bait는 금지한다.
""".strip()

BRAND="""
너는 '오늘도 한살 | MORROWAY'의 모바일 편집장이다.
이 브랜드는 특정 연령층 전용 건강계정이 아니라 '오늘을 조금 더 잘 살아가는 데 도움이 되는 생활교양 미디어'다.
몸·마음·돌봄·기억·근현대사·지명·책·음악·생활 쓸모를 한 세계관으로 묶는다.
톤은 따뜻하고 세련되며 지적이지만 잘난 척하지 않는다. 재치는 관찰형으로 한 꼬집만 쓴다.
전문성은 직함을 반복하는 대신 정확한 맥락·숫자·선택기준·현장감으로 보여준다.
간호·보건·노인복지 관찰이 유용할 때 자연스럽게 활용하되 개인 의료상담처럼 단정하지 않는다.
역사·정치·인권 주제는 사실과 의견을 구분하고 1차 자료/공공기관/학술자료/신뢰도 높은 보도를 우선한다.
'오늘도 잘 살아보자'는 정서는 남기되 같은 구호를 반복하지 않는다.
""".strip()

# ---------- free mode editorial bank ----------
# 최신 뉴스가 아니라 언제든 꺼낼 수 있는 상시형 씨앗. 최신성은 무료모드에서 사용자가 한 줄/URL로 넣는다.
FREE_IDEA_BANK=[
    dict(category="오늘의 몸", topic="혈압을 잴 때 숫자보다 먼저 확인할 것", angle="측정 자세·휴식·커프 같은 기본 조건", trigger="집에서는 혈압을 어디에서 어떻게 재는지", goal="정보형", role="신뢰 쌓기", money=62, search=88, fact=62, sens="보통"),
    dict(category="오늘의 몸", topic="약을 여러 개 먹을 때 약통보다 먼저 필요한 습관", angle="복용 목록과 처방·일반약을 한 번에 확인하는 습관", trigger="가족 약을 정리해 본 경험", goal="저장형", role="신뢰 쌓기", money=48, search=82, fact=72, sens="보통"),
    dict(category="오늘의 몸", topic="걷기 운동을 오래 가게 만드는 가장 현실적인 기준", angle="거창한 목표보다 생활동선과 지속성", trigger="걷기 습관을 만들 때 가장 어려운 것", goal="댓글형", role="사람 모으기", money=35, search=68, fact=38, sens="낮음"),
    dict(category="오늘의 몸", topic="잠이 안 올 때 침대에서 오래 버티는 게 답일까", angle="수면 습관을 생활 관점에서 살펴보기", trigger="잠 안 오는 밤에 하는 행동", goal="궁금증형", role="사람 모으기", money=35, search=78, fact=62, sens="보통"),
    dict(category="오늘의 돌봄", topic="부모님 집에 갔을 때 냉장고에서 먼저 볼 것", angle="먹을 것의 양보다 식사 패턴과 유통기한·수분 섭취 단서", trigger="부모님 집에서 가장 먼저 확인하는 것", goal="댓글형", role="신뢰 쌓기", money=55, search=82, fact=48, sens="보통"),
    dict(category="오늘의 돌봄", topic="같은 말을 반복하는 부모님, 무엇부터 관찰할까", angle="치매 단정 전에 일상 기능 변화와 반복 패턴을 살펴보기", trigger="부모님의 작은 변화를 처음 느낀 순간", goal="정보형", role="신뢰 쌓기", money=30, search=90, fact=82, sens="높음"),
    dict(category="오늘의 돌봄", topic="혼자 사는 부모님에게 매일 안부를 묻는 가장 자연스러운 질문", angle="감시가 아니라 생활 리듬을 확인하는 대화", trigger="부모님께 가장 자주 묻는 안부 문장", goal="댓글형", role="사람 모으기", money=22, search=58, fact=28, sens="낮음"),
    dict(category="오늘의 돌봄", topic="부모님 집 낙상 위험은 욕실 밖에도 많다", angle="문턱·조명·전선·신발·동선", trigger="집에서 넘어질 뻔했던 의외의 장소", goal="저장형", role="신뢰 쌓기", money=60, search=86, fact=48, sens="보통"),
    dict(category="오늘의 마음", topic="친구가 줄어드는 것과 외로운 것은 같은 말일까", angle="관계의 수보다 편안함과 연결감", trigger="지금 편하게 전화할 수 있는 사람은 몇 명인지", goal="공감형", role="사람 모으기", money=10, search=52, fact=18, sens="낮음"),
    dict(category="오늘의 마음", topic="혼자 잘 노는 능력도 나이 들수록 중요한 기술이다", angle="고립과 자발적 혼자 시간을 구분하기", trigger="혼자 있을 때 가장 좋아하는 활동", goal="댓글형", role="브랜드 세계관", money=18, search=48, fact=20, sens="낮음"),
    dict(category="오늘의 마음", topic="하루를 망쳤다고 느끼는 날, 실제로 망한 건 무엇일까", angle="성과와 하루의 가치를 분리하기", trigger="별일 없었지만 괜찮았던 하루의 장면", goal="공감형", role="브랜드 세계관", money=8, search=40, fact=12, sens="낮음"),
    dict(category="오늘의 기억", topic="삐삐가 있던 시절에는 '읽씹'이라는 고민도 없었다", angle="기술이 관계의 속도를 어떻게 바꿨는지", trigger="아직 기억나는 삐삐 암호나 공중전화 경험", goal="댓글형", role="사람 모으기", money=15, search=64, fact=35, sens="낮음"),
    dict(category="오늘의 기억", topic="90년대 직장인 책상에는 지금 당연한 것이 없었다", angle="PC·전화·팩스·서류 문화로 보는 직장생활 변화", trigger="첫 직장 책상 위에 있던 물건", goal="궁금증형", role="사람 모으기", money=18, search=74, fact=45, sens="낮음"),
    dict(category="오늘의 기억", topic="예전 여름밤은 지금보다 정말 더 시원했을까", angle="기억 속 여름 풍경과 실제 생활방식의 차이", trigger="어릴 적 여름밤 풍경 한 가지", goal="댓글형", role="사람 모으기", money=12, search=65, fact=48, sens="낮음"),
    dict(category="오늘의 기억", topic="동네 비디오가게에서 한 편을 고르던 시간이 길었던 이유", angle="선택지가 적던 시절의 기대와 기다림", trigger="주말마다 빌려보던 영화 장르", goal="공감형", role="브랜드 세계관", money=8, search=40, fact=12, sens="낮음"),
    dict(category="오늘의 역사", topic="광복 뒤 친일청산은 왜 끝까지 가지 못했을까", angle="제도·정치적 조건을 기록 중심으로 짚기", trigger="학교에서 뒤늦게 알게 된 근현대사 한 가지", goal="궁금증형", role="검색자산", money=5, search=90, fact=92, sens="높음"),
    dict(category="오늘의 역사", topic="1987년의 거리는 평범한 사람들에게 어떤 하루였을까", angle="큰 사건보다 직장·학교·가정의 생활사", trigger="가족에게 들은 1980년대의 기억", goal="공감형", role="브랜드 세계관", money=5, search=84, fact=88, sens="높음"),
    dict(category="오늘의 역사", topic="헌법은 거창한 문서가 아니라 일상 어디에 있을까", angle="표현·노동·교육·선거 같은 일상 권리로 연결", trigger="예전엔 당연하지 않았는데 지금은 당연한 권리", goal="정보형", role="브랜드 세계관", money=3, search=75, fact=72, sens="보통"),
    dict(category="오늘의 역사", topic="한 장의 가족사진으로 근현대 생활사를 읽는 법", angle="옷·간판·집·교통·가전에서 시대 단서를 읽기", trigger="집에 있는 가장 오래된 가족사진의 배경", goal="댓글형", role="사람 모으기", money=12, search=58, fact=35, sens="낮음"),
    dict(category="오늘의 동네", topic="신당동에는 정말 '신당'이 있었을까", angle="지명에 남은 생활·신앙·도시의 흔적", trigger="자기 동네 이름의 뜻을 아는지", goal="궁금증형", role="검색자산", money=18, search=88, fact=72, sens="낮음"),
    dict(category="오늘의 동네", topic="을지로의 '을지'는 누구 이름일까", angle="도로명과 역사 인물이 연결된 배경", trigger="매일 지나지만 뜻을 몰랐던 지명", goal="궁금증형", role="검색자산", money=15, search=86, fact=68, sens="낮음"),
    dict(category="오늘의 동네", topic="서울 동네 이름에는 왜 '골'과 '재'가 많을까", angle="지형과 옛길이 지명에 남는 방식", trigger="이상하다고 느꼈던 동네 이름", goal="댓글형", role="사람 모으기", money=12, search=82, fact=62, sens="낮음"),
    dict(category="오늘의 취향", topic="어떤 노래는 왜 첫 소절만으로 한 시절을 데려올까", angle="음악과 자전적 기억의 연결", trigger="전주만 들어도 특정 시절이 떠오르는 노래", goal="댓글형", role="사람 모으기", money=10, search=45, fact=22, sens="낮음"),
    dict(category="오늘의 취향", topic="책을 끝까지 읽지 않아도 남는 문장이 있다", angle="완독보다 삶에 남는 한 문장", trigger="몇 년째 기억나는 책 속 생각", goal="공감형", role="브랜드 세계관", money=10, search=42, fact=22, sens="낮음"),
    dict(category="오늘의 취향", topic="나이 들수록 여행에서 보고 싶은 것이 달라지는 순간", angle="명소보다 동네·시장·사람·휴식", trigger="예전과 달라진 여행 취향", goal="댓글형", role="사람 모으기", money=38, search=58, fact=18, sens="낮음"),
    dict(category="오늘의 쓸모", topic="혈압계 살 때 브랜드보다 먼저 볼 세 가지", angle="상완형·커프·혼자 쓰기 쉬운지 같은 선택 기준", trigger="집에서 실제로 쓰는 건강기기", goal="수익형", role="수익 연결", money=92, search=92, fact=70, sens="보통"),
    dict(category="오늘의 쓸모", topic="부모님께 사드렸는데 의외로 가장 오래 쓰는 생활용품", angle="비싼 기능보다 일상에서 실제 쓰이는 조건", trigger="사드리고 가장 잘 쓴 물건", goal="댓글형", role="수익 연결", money=80, search=70, fact=28, sens="낮음"),
    dict(category="오늘의 쓸모", topic="혼자 먹는 한 끼를 덜 귀찮게 만드는 도구는 무엇일까", angle="조리시간·설거지·보관을 줄이는 기준", trigger="혼밥할 때 가장 자주 쓰는 도구", goal="댓글형", role="수익 연결", money=82, search=74, fact=18, sens="낮음"),
    dict(category="계절·기념일", topic="계절이 바뀔 때 몸보다 먼저 달라지는 생활 리듬", angle="수면·식사·활동시간의 작은 변화", trigger="계절이 바뀌면 제일 먼저 달라지는 습관", goal="댓글형", role="사람 모으기", money=28, search=64, fact=38, sens="낮음"),
]

CATEGORY_FALLBACK={
    "오늘의 이슈":("오늘 본 뉴스 한 줄을 생활교양의 질문으로 바꾸기","기사 자체를 요약하기보다 '우리 삶에 무슨 뜻인가'를 묻는다."),
    "계절·기념일":("오늘 날짜에 붙어 있는 작은 생활사","공식 기념일·절기·계절을 억지 교훈 없이 일상으로 연결한다."),
}


def korea_today(): return datetime.now(ZoneInfo("Asia/Seoul")).date()

def get_api_key():
    try:
        import streamlit as st
        if "OPENAI_API_KEY" in st.secrets: return st.secrets["OPENAI_API_KEY"]
        if st.session_state.get("runtime_api_key"): return st.session_state.runtime_api_key
    except Exception: pass
    return os.getenv("OPENAI_API_KEY","")

def get_model(mode="절약"):
    try:
        import streamlit as st
        if "OPENAI_MODEL" in st.secrets: return str(st.secrets["OPENAI_MODEL"])
    except Exception: pass
    return os.getenv("OPENAI_MODEL",MODEL_MODES.get(mode,"gpt-5.6-luna"))

def client_for(api_key=None):
    key=api_key or get_api_key()
    if not key: raise RuntimeError("OpenAI API Key가 설정되지 않았습니다.")
    from openai import OpenAI
    return OpenAI(api_key=key)

def sources_from_response(response):
    seen=set(); out=[]
    for item in getattr(response,"output",[]) or []:
        if getattr(item,"type",None)=="web_search_call":
            action=getattr(item,"action",None)
            for s in getattr(action,"sources",[]) or []:
                u=getattr(s,"url",""); t=getattr(s,"title","") or u
                if u and u not in seen: seen.add(u); out.append({"title":t,"url":u})
        if getattr(item,"type",None)=="message":
            for content in getattr(item,"content",[]) or []:
                for ann in getattr(content,"annotations",[]) or []:
                    if getattr(ann,"type",None)=="url_citation":
                        u=getattr(ann,"url",""); t=getattr(ann,"title","") or u
                        if u and u not in seen: seen.add(u); out.append({"title":t,"url":u})
    return out

def web_research(prompt:str, model:str, api_key=None):
    c=client_for(api_key)
    r=c.responses.create(
        model=model,
        reasoning={"effort":"low"},
        tools=[{"type":"web_search","search_context_size":"low","user_location":{"type":"approximate","country":"KR","city":"Seoul","region":"Seoul"}}],
        tool_choice="auto",
        include=["web_search_call.action.sources"],
        input=prompt,
    )
    return r.output_text, sources_from_response(r)

def parse_model(cls:Type[BaseModel], prompt:str, model:str, api_key=None, system_extra=""):
    c=client_for(api_key)
    r=c.responses.parse(
        model=model,
        reasoning={"effort":"low"},
        input=[
            {"role":"system","content":BRAND+"\n\n"+THREADS_OFFICIAL_SIGNALS+"\n\n"+system_extra},
            {"role":"user","content":prompt},
        ],
        text_format=cls,
    )
    if r.output_parsed is None: raise RuntimeError("구조화된 결과를 받지 못했습니다.")
    return r.output_parsed

def calendar_context(target_date:str, window=4):
    try: target=date.fromisoformat(target_date)
    except Exception: return []
    rows=json.loads(CAL_PATH.read_text(encoding="utf-8")) if CAL_PATH.exists() else []
    out=[]
    for row in rows:
        try:
            d=date(target.year,int(row["month"]),int(row["day"])); delta=(d-target).days
            if abs(delta)<=window: out.append({**row,"days_from_target":delta})
        except Exception: pass
    return sorted(out,key=lambda x:abs(x["days_from_target"]))

# ---------- zero-API helpers ----------
def _stable_num(text, lo=0, hi=12):
    n=int(hashlib.md5(text.encode("utf-8")).hexdigest()[:6],16)
    return lo + n % (hi-lo+1)

def _clip(v): return max(0,min(100,int(v)))

def _hook_for(topic,category):
    if category=="오늘의 동네": return f"매일 지나면서도 몰랐다. {topic}"
    if category=="오늘의 역사": return f"교과서 한 줄보다 궁금한 건 이거다. {topic}"
    if category=="오늘의 기억": return f"이 장면 기억나면 이야기가 길어진다. {topic}"
    if category=="오늘의 몸": return f"건강정보보다 먼저 확인해볼 것. {topic}"
    if category=="오늘의 돌봄": return f"부모님을 챙길 때 의외로 먼저 보게 되는 것. {topic}"
    if category=="오늘의 쓸모": return f"돈 쓰기 전에 이 기준부터. {topic}"
    return topic

def _candidate_from_seed(seed,target_date,why_prefix=""):
    jitter=_stable_num(target_date+seed["topic"],0,8)
    base_cur=76+jitter
    reach=base_cur + (7 if seed["goal"] in ["댓글형","궁금증형"] else 0)
    conv=78+jitter if seed["goal"] in ["댓글형","공감형","설문형"] else 62+jitter
    save=82+jitter if seed["goal"] in ["정보형","저장형","수익형"] else 58+jitter
    return Candidate(
        topic=seed["topic"], category=seed["category"],
        why_now=(why_prefix+" "+("오늘도 꺼내기 좋은 상시형 생활교양 소재." if not why_prefix else "")).strip(),
        angle=seed["angle"], curiosity_hook=_hook_for(seed["topic"],seed["category"]),
        conversation_trigger=seed["trigger"], suggested_goal=seed["goal"], asset_role=seed["role"],
        reach_score=_clip(reach), conversation_score=_clip(conv), curiosity_score=_clip(base_cur),
        save_score=_clip(save), share_score=_clip((reach+conv)//2), search_asset_score=seed["search"],
        monetization_score=seed["money"], evergreen_score=_clip(72+jitter), fact_risk=seed["fact"],
        sensitivity=seed["sens"], risk_note="무료모드 점수는 편집용 휴리스틱. 최신·의학·역사 사실은 게시 전 확인.", source_refs=[]
    )

def _category_from_type(t):
    s=str(t)
    if "역사" in s or "민주" in s: return "오늘의 역사"
    if "돌봄" in s or "복지" in s: return "오늘의 돌봄"
    if "건강" in s or "안전" in s: return "오늘의 몸"
    if "마음" in s: return "오늘의 마음"
    if "문화" in s: return "오늘의 기억"
    return "계절·기념일"

def free_candidate_board(target_date,categories,pattern="균형 편집판",manual="",n=5):
    cats=list(categories or CATEGORIES)
    out=[]; used=set()
    cal=calendar_context(target_date,window=4)
    # 주변 공식 캘린더를 먼저 반영
    for row in cal:
        cat=_category_from_type(row.get("type",""))
        if cat not in cats: continue
        delta=row.get("days_from_target",0)
        rel="오늘" if delta==0 else (f"{delta}일 뒤" if delta>0 else f"{abs(delta)}일 전")
        for idea in row.get("ideas",[])[:2]:
            seed=dict(category=cat,topic=idea,angle=f"{row.get('label')}을 큰 교훈보다 평범한 사람의 생활과 연결",trigger=f"{row.get('label')}과 연결해 기억나는 개인·가족의 경험",goal="궁금증형" if cat=="오늘의 역사" else "댓글형",role="브랜드 세계관",money=8,search=82,fact=78 if cat=="오늘의 역사" else 45,sens="높음" if cat=="오늘의 역사" else "보통")
            c=_candidate_from_seed(seed,target_date,f"{row.get('label')}이(가) {rel}이라 자연스럽게 연결된다.")
            if c.topic not in used: out.append(c); used.add(c.topic)
    # 사용자가 지정한 소재는 최우선
    if manual.strip():
        cat=cats[0] if cats else "오늘의 기억"
        seed=dict(category=cat,topic=manual.strip(),angle="사용자가 오늘 직접 관심을 둔 소재에서 구체적 질문 하나만 파기",trigger="이 소재와 연결된 자신의 경험·지역·세대 기억",goal="궁금증형",role="사람 모으기",money=35,search=60,fact=65 if cat in ["오늘의 역사","오늘의 몸","오늘의 이슈"] else 35,sens="보통")
        c=_candidate_from_seed(seed,target_date,"사용자가 오늘 지정한 소재.")
        out.insert(0,c); used.add(c.topic)
    # 패턴에 따라 정렬 가중치
    pool=[s for s in FREE_IDEA_BANK if s["category"] in cats and s["topic"] not in used]
    prefs=[]
    if "역사" in pattern: prefs=["오늘의 역사","오늘의 동네","오늘의 기억"]
    elif "몸과" in pattern: prefs=["오늘의 몸","오늘의 돌봄","오늘의 쓸모"]
    elif "추억" in pattern: prefs=["오늘의 기억","오늘의 취향","오늘의 동네"]
    elif "수익" in pattern: prefs=["오늘의 쓸모","오늘의 몸","오늘의 돌봄"]
    elif "오늘 뭐" in pattern: prefs=["계절·기념일","오늘의 기억","오늘의 몸","오늘의 돌봄"]
    def score_seed(s):
        pref=(len(prefs)-prefs.index(s["category"]))*100 if s["category"] in prefs else 0
        return pref + _stable_num(target_date+s["topic"],0,99)
    pool=sorted(pool,key=score_seed,reverse=True)
    for s in pool:
        if len(out)>=n: break
        out.append(_candidate_from_seed(s,target_date))
    # 부족하면 fallback
    while len(out)<n:
        cat=cats[len(out)%len(cats)] if cats else "오늘의 기억"
        topic,angle=CATEGORY_FALLBACK.get(cat,(f"{cat}에서 오늘 한 가지 궁금한 것", "한 번에 질문 하나만 파고든다."))
        seed=dict(category=cat,topic=topic,angle=angle,trigger="내 경험 한 장면으로 답할 수 있는 질문",goal="댓글형",role="사람 모으기",money=20,search=50,fact=40,sens="낮음")
        out.append(_candidate_from_seed(seed,target_date))
    return CandidateBoard(target_date=target_date, editorial_note="🆓 무료 편집판: API 호출 없이 내장 저널·기념일·상시형 소재를 조합했습니다. 최신 이슈는 직접 한 줄/URL을 넣으면 ChatGPT용 프롬프트로 연결됩니다.", candidates=out[:n])

def free_hook_suggestions(topic,category,goal="궁금증형"):
    t=topic.strip()
    if goal=="댓글형":
        return [f"{t} — 여러분은 어떤 장면이 먼저 떠오르세요?", f"이 얘기는 세대마다 답이 다르다. {t}", f"사소해 보여도 사람마다 경험이 갈리는 것. {t}"]
    if goal=="정보형" or goal=="저장형":
        return [f"{t}, 이것부터 확인하면 덜 헷갈린다.", f"복잡하게 말할 필요 없다. {t}의 핵심은 세 가지다.", f"알아두면 언젠가 한 번은 써먹는다. {t}"]
    if goal=="수익형":
        return [f"{t}, 사기 전에 기준부터 세우자.", f"비싼 걸 고르기 전에 먼저 볼 것. {t}", f"제품보다 선택 기준이 먼저다. {t}"]
    return [f"{t}, 왜 그런 걸까?", f"우리는 {t}을 안다고 생각하지만 설명하려면 잠깐 멈칫한다.", f"의외로 이야기할수록 궁금해지는 것. {t}"]

def free_threads_prompt(topic,category,goal,target_date,angle="",conversation_trigger="",experience_note="",current_issue="",source_url="",sensitivity="보통"):
    hooks="\n".join("- "+x for x in free_hook_suggestions(topic,category,goal))
    verify = category in ["오늘의 몸","오늘의 역사","오늘의 이슈"] or sensitivity=="높음" or bool(source_url)
    verification = "필요한 최신·의학·역사 사실은 반드시 웹 검색으로 검증하고, 출처 2~4개를 답변 맨 아래에 짧게 정리해줘." if verify else "최신 사실이 필요한 부분은 단정하지 말고, 필요하면 웹 검색으로 확인해줘."
    return f"""너는 Threads 생활교양 미디어 '오늘도 한살 | MORROWAY'의 편집장이다.
오늘 날짜: {target_date}
주제: {topic}
카테고리: {category}
목적: {goal}
각도: {angle or '한 게시물에 질문 하나, 핵심 하나'}
독자 대화 방아쇠: {conversation_trigger or '자기 경험을 한 문장으로 답할 수 있는 구체적 질문'}
내 경험/관찰: {experience_note or '없음'}
오늘 본 이슈/기사 한 줄: {current_issue or '없음'}
참고 URL: {source_url or '없음'}
민감도: {sensitivity}

브랜드 톤:
- 따뜻하고 지적이지만 선생님처럼 훈계하지 않는다.
- 전문성은 어려운 용어보다 구체적인 맥락·숫자·선택 기준으로 보여준다.
- 위트는 생활·추억에서 관찰형으로 한 꼬집. 피해·참사·중증질환·인권침해에는 유머 금지.
- 정치·역사 소재는 사실/해석/의견을 구분한다.
- 건강 소재는 개인 진단·처방처럼 단정하지 않는다.
- '충격/소름/당신만 모름/반드시 보세요' 같은 낚시는 금지한다.

내가 생각한 훅 뼈대:
{hooks}

완성해야 할 것:
1) 실제 첫줄로 쓸 후킹 5개. 궁금증은 만들되 거짓 빈칸은 금지.
2) 가장 좋은 1개를 골라 Threads 본문 180~430자. 첫 2~4문장 안에 훅의 약속을 갚기.
3) 본문 끝에 억지 질문을 붙이지 말고, 자연스럽다면 자기 경험을 쉽게 말할 수 있는 질문 3개 제안.
4) 작성자가 자기 글 아래 먼저 달 수 있는 첫 댓글 3개: 보충사실 / 내 경험 / 추가 질문.
5) Threads topic 후보 1개(# 없이).
6) 게시 전 팩트체크 포인트 3개 이하.
7) 제휴가 자연스러운 소재라면 '제품 추천'보다 '고르는 기준'으로 연결하는 방법 1줄. 억지면 '제휴 없음'.
8) 마지막에 '왜 이 글이 댓글을 부르는지' 한 문장으로 설명.

{verification}
문장을 베끼지 말고 오늘도 한살만의 원고로 써줘."""

def free_issue_prompt(issue_text,source_url="",target_date=None):
    target_date=target_date or korea_today().isoformat()
    return f"""오늘 날짜는 {target_date}. 아래 최신 이슈를 '오늘도 한살 | MORROWAY' 세계관에 맞는 Threads 소재로 바꿔줘.
이슈/기사 한 줄: {issue_text}
URL: {source_url or '없음'}

먼저 웹에서 사실을 확인한 뒤 다음을 제안해줘:
- 단순 뉴스 요약이 아닌 생활교양 각도 5개
- 각 각도별 첫줄 2개
- 댓글이 자연스럽게 달릴 구체적 경험 질문 1개
- 건강/돌봄/역사/생활/추억/쓸모 중 맞는 카테고리
- 팩트 위험도와 게시 전 확인사항
정치·재난·피해 사건은 정파적 선동이나 피해 소비 없이 기록·맥락·사람의 삶 중심으로 다뤄줘."""

def free_reply_prompt(mode,source_text,comment_text,voice_note=""):
    task="내 Threads 글에 달린 댓글에 답장" if mode=="내 글 댓글 답장" else "다른 사람 Threads 글에 의미 있는 댓글"
    return f"""'오늘도 한살 | MORROWAY' 톤으로 {task}을 도와줘.
원글/맥락: {source_text}
댓글 또는 반응할 문장: {comment_text}
내가 꼭 넣고 싶은 말: {voice_note or '없음'}

서로 확실히 다른 답글 4개를 만들어줘:
1) 따뜻한 공감형 2) 정보 한 스푼형 3) 질문으로 확장형 4) 짧고 재치 있는 형(민감한 주제면 재치 금지).
'좋은 글 감사합니다' 같은 빈말, 자기홍보, 논쟁을 위한 논쟁은 금지. 사실을 새로 추가해야 한다면 먼저 웹에서 검증해줘."""

def free_expand_prompt(topic,final_text,channels,experience_note=""):
    return f"""다음 Threads 원고를 플랫폼별로 '복붙'이 아니라 새로 편집해줘.
주제: {topic}
원고: {final_text}
확장 채널: {', '.join(channels)}
내 경험/사진/관찰: {experience_note or '없음'}

- 네이버 블로그: 국내 검색 의도, 소제목, 체크리스트, 현장관찰.
- AdSense 독립블로그: 사람우선 장문. 원자료·직접 경험·사진·표·체크리스트 중 최소 2개를 넣을 자리 표시.
- YouTube Shorts: 35~55초, 2초 훅→정보 3~5비트→여운 엔딩, 자막 친화.
- Instagram: 저장형 카드뉴스 5~8장 또는 캡션.
각 채널마다 제목 후보, 본문/대본, 사실검수, 사람이 직접 보태야 할 고유가치, 수익화 가능성까지 정리해줘."""

def free_money_map(topic,category,search_score=50,monetization_score=50,fact_risk=30):
    routes=[]
    # 간단한 편집 휴리스틱. 실제 수익 예측이 아님.
    affiliate=_clip(monetization_score + (12 if category in ["오늘의 쓸모","오늘의 몸","오늘의 돌봄"] else -15))
    search=_clip(search_score + (10 if category in ["오늘의 역사","오늘의 동네","오늘의 몸","오늘의 돌봄"] else 0))
    pdf=_clip((search+monetization_score)//2 + (8 if category in ["오늘의 돌봄","오늘의 역사","오늘의 동네"] else 0))
    video=_clip(65 + (10 if category in ["오늘의 기억","오늘의 역사","오늘의 동네","오늘의 취향"] else 0))
    brand=_clip(48 + (10 if category in ["오늘의 쓸모","오늘의 몸","오늘의 돌봄"] else 0))
    if fact_risk>75: affiliate=max(0,affiliate-25); brand=max(0,brand-15)
    rows=[("제휴",affiliate,"제품보다 선택 기준을 먼저 주는 글"),("네이버/구글 광고",search,"검색 질문을 장문 자산으로 확장"),("자체 PDF·전자책",pdf,"체크리스트·지도·가이드처럼 묶기"),("유튜브 확장",video,"짧은 이야기 구조로 쇼츠화"),("브랜드 협업",brand,"신뢰가 쌓인 뒤 관련 생활 브랜드와 연결"),("검색자산",search,"오래 검색될 질문으로 축적")]
    rows=sorted(rows,key=lambda x:x[1],reverse=True)
    return {"topic":topic,"money_score":max(affiliate,pdf,brand),"audience_value_score":_clip((search+video+70)//3),"best_route":rows[0][0],"routes":rows,"warning":"무료 MONEY RADAR는 휴리스틱입니다. 역사·인권·피해·질병 불안을 상품 판매에 이용하지 않습니다.","next_asset":f"{topic}을(를) {rows[0][2]} 방향의 다음 콘텐츠로 확장"}

# ---------- paid mode prompts ----------
def research_prompt(target_date,categories,pattern,manual,cal):
    return f"""
오늘도 한살의 {target_date} 편집회의용 사실 조사를 한다.
선택 카테고리: {', '.join(categories)}
편집판: {pattern}
사용자 관심 소재: {manual or '없음'}
기준일 주변 내장 캘린더: {json.dumps(cal,ensure_ascii=False)}

조사 우선순위:
1) 기준일의 계절·절기·공식 기념일·역사적 기념일
2) 최근 24~72시간 한국 이슈 중 건강/돌봄/생활/문화/역사와 실제 연결 가치가 있는 것
3) 기준일 전후의 근현대사·생활사·지명·문화·추억
4) 계절성 건강·안전·돌봄 공공 권고
5) 상시형이지만 지금 다시 꺼내면 좋은 생활교양

연예인 가십, 확인 안 된 바이럴, 공포를 이용한 건강상술은 제외한다.
정치·역사·의학은 사실검증에 쓸 원자료 후보까지 메모한다.
현재 일어난 사건과 '오늘 보도된 과거 사건'을 혼동하지 않는다.
""".strip()

def board_prompt(target_date,categories,pattern,manual,research,sources,n):
    src="\n".join(f"[{i+1}] {s['title']} | {s['url']}" for i,s in enumerate(sources)) or "웹 조사 출처 없음"
    return f"""
기준일 {target_date}. 아래 조사로 서로 겹치지 않는 Threads 소재 후보를 정확히 {n}개 만든다.
카테고리: {', '.join(categories)} / 편집판: {pattern} / 특별주제: {manual or '없음'}

[조사 메모]\n{research[:7000]}
[출처]\n{src}

각 소재는 '왜 지금', 독자가 얻는 쓸모, 어떤 경험/의견을 댓글로 말하고 싶어지는지까지 설계한다.
conversation_trigger는 '의견 있으세요?' 같은 범용 문장이 아니라 독자가 쉽게 자기 경험을 꺼낼 구체적 방아쇠다.
suggested_goal은 댓글형/궁금증형/공감형/정보형/저장형/수익형/설문형/확장형 중 가장 맞는 하나.
asset_role은 사람 모으기/신뢰 쌓기/검색자산/수익 연결/브랜드 세계관 중 하나.
점수는 0~100의 편집 보조값이며 성과 보장이 아니다.
fact_risk는 검수 난이도이며 높을수록 위험하다. source_refs는 실제 근거로 쓴 출처 번호만 넣는다.
민감한 인권·참사·피해·중증질환은 sensitivity=높음, 위트 금지.
""".strip()

def draft_prompt(topic,category,goal,angle,why_now,research,sources,sensitivity="보통",experience_note=""):
    src="\n".join(f"[{i+1}] {s['title']} | {s['url']}" for i,s in enumerate(sources)) or "웹 조사 출처 없음"
    style=style_profile_brief()
    return f"""
아래 소재를 '오늘도 한살' Threads 게시물 1개로 만든다.
주제: {topic}
카테고리: {category}
목적: {goal}
각도: {angle}
왜 지금: {why_now}
민감도: {sensitivity}
사용자가 보태고 싶은 경험/관찰: {experience_note or '없음'}

[조사]\n{research[:6000]}
[출처]\n{src}
[벤치마크에서 추상화한 문법]\n{style[:2500]}

필수 편집 규칙:
- hooks 7개. 자극적 낚시 대신 '정보의 빈칸'을 만든다.
- 첫 2~4문장 안에서 훅의 약속을 갚는다.
- 기본 본문은 한국어 약 180~430자. 한 게시물에 핵심 하나만.
- 댓글형이면 독자가 자신의 경험·지역·세대·선택·기억을 쉽게 말할 수 있는 구체적 질문을 만든다.
- first_reply_options는 작성자가 자기 글 아래 첫 답글로 붙일 수 있는 보충사실/내 경험/추가 질문 3개.
- topic_tag는 주제 후보 딱 1개. #기호 없이.
- 건강정보는 개인 진단/치료 지시가 아니라 일반 정보와 진료 필요 신호를 구분한다.
- 역사/정치/인권은 사실·해석·의견을 구분한다.
- 민감도 높음은 위트 0, 존엄 우선.
""".strip()

def quick_research_prompt(target_date,topic,category):
    return f"""{target_date} 한국 기준. 오늘도 한살 Threads 글 '{topic or '오늘과 연결된 생활교양 한 가지'}'를 쓰기 위한 최소 사실조사를 한다. 카테고리 {category}. 최신성·의학·역사·정치 사실이 있으면 신뢰할 수 있는 원자료를 우선하고 게시 전 확인할 숫자/날짜를 명확히 적어라."""

def rewrite_prompt(final_text,topic,category,goal,action,sensitivity):
    return f"""
다음 Threads 초안을 '{action}' 방향으로 다시 편집한다.
주제: {topic} / 카테고리: {category} / 원래 목적: {goal} / 민감도: {sensitivity}
[현재 초안]\n{final_text}
사실을 새로 지어내지 않는다. 훅은 강화하되 낚시/과장/분노유도 금지. 댓글성을 높일 때는 답하기 쉬운 구체적 경험 질문. 본문은 가능하면 180~430자. hook/body/closing/question/first_reply를 완성한다.
""".strip()

def review_prompt(final_text,topic,category,goal,sensitivity):
    return f"""
다음 Threads 원고를 모바일 편집장처럼 냉정하게 감수한다.
주제 {topic} / 카테고리 {category} / 목적 {goal} / 민감도 {sensitivity}
[원고]\n{final_text}
평가축: hook, curiosity, payoff, expertise, usefulness, conversation, shareability, originality, total. conversation은 질문 존재 여부가 아니라 사람이 자연스럽게 자기 경험을 말하고 싶은가를 본다. clickbait_risk도 평가하고 더 구체적이고 약속을 빨리 갚는 수정안을 만든다.
""".strip()

def reply_prompt(mode,source_text,comment_text,voice_note=""):
    if mode=="내 글 댓글 답장": task="내 Threads 글에 달린 댓글에 답한다. 상대를 존중하면서 대화를 한 단계 더 깊게 이어간다."
    else: task="다른 사람 Threads 글에 의미 있는 답글을 단다. 홍보나 자기소개가 아니라 상대 글에 실제 가치를 더한다."
    return f"""{task}\n원글/맥락: {source_text}\n댓글 또는 답할 내용: {comment_text}\n내가 넣고 싶은 한마디: {voice_note or '없음'}\n서로 확실히 다른 답글 3~5개를 만든다. 빈말·조롱·검증되지 않은 새 사실 금지.""".strip()

def money_prompt(topic,category,why_now,search_score=50,monetization_score=50,fact_risk=30):
    return f"""오늘도 한살 소재의 수익화 경로를 설계한다. 주제: {topic} / 카테고리: {category} / 왜 지금: {why_now}. 검색자산성 {search_score}/100, 직접수익성 {monetization_score}/100, 팩트위험 {fact_risk}/100. 제휴/광고/자체 PDF·전자책/유튜브/브랜드/검색자산을 분리 평가한다. 독자가치가 수익보다 먼저다.""".strip()

def platform_prompt(topic,final_text,channels,experience_note=""):
    return f"""다음 Threads 원고를 {', '.join(channels)}에 맞게 각각 새로 편집한다. 문장 복제/길이 늘리기 금지. 주제: {topic}\nThreads 원고: {final_text}\n사람이 더할 경험/관찰: {experience_note or '없음'}\n각 플랫폼의 검색·시청 의도에 맞춰 제목, 원고, 사람이 더할 고유가치, 사실검수, 수익화 메모를 만든다.""".strip()

def top100_prompt(payload,n):
    return f"""아래는 사용자가 수집한 공개 Threads 우수 게시물 벤치마크 최대 100개다. 전세계 공식 Top100이 아니다. 샘플 {n}개.\n{payload}\n원문 고유 표현을 재작성하거나 복제하지 말고 일반 패턴만 추상화한다. 첫줄, 문장 호흡, 정보밀도, 관찰형 위트, 전문성, 실용정보, 답글 유도를 나눈다. 혐오·분노유도·검증되지 않은 단정은 anti-pattern으로 분리한다.""".strip()

def build_final_text(hook,body,closing="",question="",topic_tag="",affiliate=False):
    parts=[hook.strip(),"",body.strip()]
    if closing.strip(): parts.extend(["",closing.strip()])
    if question.strip(): parts.extend(["",question.strip()])
    if affiliate: parts.extend(["","※ 이 글에는 제휴 링크가 포함되어 있으며, 링크를 통한 구매 시 일정 수수료를 받을 수 있습니다."])
    return "\n".join(parts).strip()
