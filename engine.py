from __future__ import annotations
import json, os
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Type
from pydantic import BaseModel
from models import *
from top100_lab import style_profile_brief

ROOT=Path(__file__).parent
CAL_PATH=ROOT/"editorial_calendar.json"

CATEGORIES=[
    "오늘의 몸","오늘의 돌봄","오늘의 마음","오늘의 기억","오늘의 역사",
    "오늘의 동네","오늘의 취향","오늘의 쓸모","계절·기념일","오늘의 이슈"
]
GOALS=["댓글형","궁금증형","공감형","정보형","저장형","수익형","설문형","확장형"]
JOURNAL_PATTERNS={
    "균형 편집판":"건강·돌봄·역사·지명·추억·생활 쓸모를 고르게 섞는다.",
    "오늘 뭐 있지?":"기준일 계절·기념일·최근 72시간 이슈를 우선하되 억지로 연결하지 않는다.",
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
Threads 운영에 반영할 공식 공개 신호:
- Meta는 답글이 Threads 조회의 거의 절반을 차지한다고 공개했다. 따라서 일방적 방송보다 진짜 대화가 생길 글을 우선한다.
- 대화를 유도하는 게시물이 추천될 가능성이 높다고 안내한다.
- 유머가 있는 콘텐츠는 평균적으로 더 많은 조회를 받는 경향이 있지만, 피해·참사·질병·죽음·인권 침해에는 유머를 쓰지 않는다.
- 상위 크리에이터는 Threads 전용 오리지널 콘텐츠를 만드는 경향이 있다. 타 플랫폼 문장을 그대로 복사하지 않는다.
- 주제(topic)를 태그한 게시물이 평균적으로 더 많은 조회를 받았다는 Meta 내부 데이터가 있다. 게시물당 topic 제안은 정확히 1개만 한다.
이 신호들은 성공 보장이 아니라 편집 원칙이다. 억지 댓글 유도, 분노 유도, 거짓 낚시, '댓글 남겨주세요/팔로우해주세요' 같은 engagement bait는 금지한다.
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


def korea_today(): return datetime.now(ZoneInfo("Asia/Seoul")).date()

def get_api_key():
    try:
        import streamlit as st
        if "OPENAI_API_KEY" in st.secrets: return st.secrets["OPENAI_API_KEY"]
        if st.session_state.get("runtime_api_key"): return st.session_state.runtime_api_key
    except Exception: pass
    return os.getenv("OPENAI_API_KEY","")

def get_model(mode="균형"):
    try:
        import streamlit as st
        if "OPENAI_MODEL" in st.secrets: return str(st.secrets["OPENAI_MODEL"])
    except Exception: pass
    return os.getenv("OPENAI_MODEL",MODEL_MODES.get(mode,"gpt-5.6-terra"))

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
        tools=[{"type":"web_search","search_context_size":"medium","user_location":{"type":"approximate","country":"KR","city":"Seoul","region":"Seoul"}}],
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

[조사 메모]\n{research[:12000]}
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

[조사]\n{research[:10000]}
[출처]\n{src}
[벤치마크에서 추상화한 문법]\n{style}

필수 편집 규칙:
- hooks 7개. 첫줄로 바로 써도 자연스러워야 한다. 자극적 낚시 대신 '정보의 빈칸'을 만든다.
- 첫 2~4문장 안에서 훅의 약속을 갚는다. 제목만 세고 본문이 약하면 실패다.
- 기본 본문은 한국어 약 180~430자. 한 게시물에 핵심 하나만.
- first_lines는 훅 다음 두 번째 문장 대안 3개.
- 댓글형이면 독자가 자신의 경험·지역·세대·선택·기억을 쉽게 말할 수 있는 구체적 질문을 만든다.
- 질문이 억지로 보이면 질문 대신 여운을 택할 수 있지만 discussion_questions에는 후보를 제공한다.
- first_reply_options는 작성자가 자기 글 아래 첫 답글로 붙일 수 있는 '보충사실/내 경험/추가 질문' 3개. 본문 반복 금지.
- source_reply는 건강·역사·정치·핫이슈처럼 검증이 중요한 경우 출처 종류를 짧게 밝혀주는 첫 답글용 문구. URL을 날조하지 않는다.
- save_line/share_line은 꼭 필요할 때만. '저장하세요/공유하세요' 구걸 문구 대신 왜 보관 가치가 있는지 자연스럽게 표현.
- topic_tag는 Threads에 붙일 주제 후보 딱 1개. #기호 없이 실제 검색 가능한 짧은 한국어 주제로.
- 설문에 잘 맞으면 poll.suitable=true, 질문과 2~4개 짧은 선택지. 아니면 false.
- affiliate_fit/angle은 제품부터 팔지 말고 고르는 기준과 문제 해결을 먼저 둔다.
- 건강정보는 개인 진단/치료 지시가 아니라 일반 정보와 진료 필요 신호를 구분한다.
- 역사/정치/인권은 사실·해석·의견을 구분한다.
- 민감도 높음은 위트 0, 존엄 우선.
- scores는 초안 자체에 대한 편집 추정치. 댓글 수/조회수 보장이 아니다.
""".strip()

def quick_research_prompt(target_date,topic,category):
    return f"""{target_date} 한국 기준. 오늘도 한살 Threads 글 ' {topic or '오늘과 연결된 생활교양 한 가지'} '를 쓰기 위한 최소 사실조사를 한다. 카테고리 {category}. 최신성·의학·역사·정치 사실이 있으면 신뢰할 수 있는 원자료를 우선하고, 게시 전 확인할 숫자/날짜를 명확히 적어라."""

def rewrite_prompt(final_text,topic,category,goal,action,sensitivity):
    return f"""
다음 Threads 초안을 '{action}' 방향으로 다시 편집한다.
주제: {topic} / 카테고리: {category} / 원래 목적: {goal} / 민감도: {sensitivity}

[현재 초안]\n{final_text}

규칙:
- 사실을 새로 지어내지 않는다.
- 훅의 빈칸은 강화하되 낚시/과장/분노유도 금지.
- 댓글성을 높일 때는 '댓글 남겨주세요'가 아니라 답하기 쉬운 구체적 경험 질문을 쓴다.
- 재치를 높일 때는 관찰형 위트. 민감도 높음이면 유머를 추가하지 않는다.
- 전문성을 높일 때 어려운 용어보다 구체성과 조건을 높인다.
- 본문은 가능하면 180~430자.
- hook/body/closing/question/first_reply를 완성한다.
""".strip()

def review_prompt(final_text,topic,category,goal,sensitivity):
    return f"""
다음 Threads 원고를 모바일 편집장처럼 냉정하게 감수한다.
주제 {topic} / 카테고리 {category} / 목적 {goal} / 민감도 {sensitivity}
[원고]\n{final_text}

평가축: hook, curiosity, payoff, expertise, usefulness, conversation, shareability, originality, total.
conversation은 질문 존재 여부가 아니라 '사람이 자연스럽게 자기 경험을 말하고 싶은가'를 본다.
clickbait_risk는 거짓 빈칸·과장 단정·본문이 약속을 못 갚는 정도다.
question_is_natural은 질문이 본문에서 자연스럽게 나오는지 본다.
수정안은 더 세게가 아니라 더 구체적이고 더 궁금하며 약속을 더 빨리 갚게 한다.
민감도 높음은 위트 추가 금지.
""".strip()

def reply_prompt(mode,source_text,comment_text,voice_note=""):
    if mode=="내 글 댓글 답장":
        task="내 Threads 글에 달린 댓글에 답한다. 상대를 존중하면서 대화를 한 단계 더 깊게 이어간다."
    else:
        task="다른 사람 Threads 글에 의미 있는 답글을 단다. 홍보나 자기소개가 아니라 상대 글에 실제 가치를 더한다."
    return f"""
{task}
원글/맥락: {source_text}
댓글 또는 답할 내용: {comment_text}
내가 넣고 싶은 한마디: {voice_note or '없음'}

서로 확실히 다른 답글 3~5개를 만든다: 따뜻한 공감형, 정보 한 스푼형, 질문으로 확장형 등을 섞는다.
짧고 인간적인 한국어. '좋은 글 감사합니다' 같은 빈말만 쓰지 않는다.
건강/역사/정치 사실은 새 숫자나 사실을 함부로 추가하지 않는다.
상대가 공격적이어도 맞받아 조롱하지 않는다. 논쟁이 가치 없으면 짧게 경계를 세우는 옵션도 가능하다.
""".strip()

def money_prompt(topic,category,why_now,search_score=50,monetization_score=50,fact_risk=30):
    return f"""
오늘도 한살 소재의 수익화 경로를 설계한다.
주제: {topic} / 카테고리: {category} / 왜 지금: {why_now}
검색자산성 참고 {search_score}/100, 직접수익성 참고 {monetization_score}/100, 팩트위험 {fact_risk}/100.

제휴/네이버·구글 광고/자체 PDF·전자책/유튜브 확장/브랜드 협업/검색자산을 분리 평가한다.
독자가치가 수익보다 먼저다. 역사·인권·피해자 기억 소재에는 억지 상품 판매 금지.
건강은 불안을 자극해 제품을 팔지 않는다. '오늘 글 → 다음 자산'으로 현실적인 next_asset 하나를 제안한다.
""".strip()

def platform_prompt(topic,final_text,channels,experience_note=""):
    return f"""
다음 Threads 원고를 {', '.join(channels)}에 맞게 각각 새로 편집한다. 문장 복제/길이 늘리기 금지.
주제: {topic}
Threads 원고: {final_text}
사람이 더할 경험/관찰: {experience_note or '없음'}

naver_blog=국내 검색 의도, 소제목/체크리스트/현장관찰.
adsense_blog=독립사이트 사람우선 장문, 원자료·경험·사진·표·체크리스트 중 최소 2개를 human_value_add에 요구.
youtube_shorts=35~55초, 2초 훅→3~5 정보비트→여운 엔딩, 자막 친화.
instagram=저장형 카드뉴스 5~8장 또는 캡션.
모든 초안에 사람이 더할 고유가치와 사실검수, 수익화 메모를 넣는다.
""".strip()

def top100_prompt(payload,n):
    return f"""
아래는 사용자가 수집한 공개 Threads 우수 게시물 벤치마크 최대 100개다. 전세계 공식 Top100이 아니다.
샘플 {n}개.
{payload}

원문 고유 표현을 재작성하거나 복제하지 말고, 데이터셋 안에서 상대적으로 반응이 강한 글의 일반 패턴만 추상화한다.
첫 1~2줄, 문장 호흡, 정보밀도, 반전·질문·숫자, 관찰형 위트, 전문성 신호, 실용 정보, 답글 유도 방식을 나눈다.
좋아요보다 replies/reposts도 중요하게 보되 계정 규모를 모르면 절대 비교라고 말하지 않는다.
오늘도 한살 건강·돌봄·역사·지명·추억에 쓸 일반 레시피로 번역한다.
혐오·분노유도·검증되지 않은 단정·억지 질문은 anti-pattern으로 분리한다.
""".strip()

def build_final_text(hook,body,closing="",question="",topic_tag="",affiliate=False):
    parts=[hook.strip(),"",body.strip()]
    if closing.strip(): parts.extend(["",closing.strip()])
    if question.strip(): parts.extend(["",question.strip()])
    # Topic은 Threads 작성 화면에서 별도 태그하는 것을 권장하므로 본문에는 강제로 #을 붙이지 않는다.
    if affiliate:
        parts.extend(["","※ 이 글에는 제휴 링크가 포함되어 있으며, 링크를 통한 구매 시 일정 수수료를 받을 수 있습니다."])
    return "\n".join(parts).strip()
