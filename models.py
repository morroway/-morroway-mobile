from __future__ import annotations
from typing import List, Literal
from pydantic import BaseModel, Field

Category = Literal[
    "오늘의 몸", "오늘의 돌봄", "오늘의 마음", "오늘의 기억", "오늘의 역사",
    "오늘의 동네", "오늘의 취향", "오늘의 쓸모", "계절·기념일", "오늘의 이슈"
]
Goal = Literal["댓글형", "궁금증형", "공감형", "정보형", "저장형", "수익형", "설문형", "확장형"]
AssetRole = Literal["사람 모으기", "신뢰 쌓기", "검색자산", "수익 연결", "브랜드 세계관"]
Sensitivity = Literal["낮음", "보통", "높음"]

class Candidate(BaseModel):
    topic: str
    category: Category
    why_now: str
    angle: str
    curiosity_hook: str
    conversation_trigger: str
    suggested_goal: Goal
    asset_role: AssetRole
    reach_score: int = Field(ge=0, le=100)
    conversation_score: int = Field(ge=0, le=100)
    curiosity_score: int = Field(ge=0, le=100)
    save_score: int = Field(ge=0, le=100)
    share_score: int = Field(ge=0, le=100)
    search_asset_score: int = Field(ge=0, le=100)
    monetization_score: int = Field(ge=0, le=100)
    evergreen_score: int = Field(ge=0, le=100)
    fact_risk: int = Field(ge=0, le=100)
    sensitivity: Sensitivity
    risk_note: str
    source_refs: List[int] = []

class CandidateBoard(BaseModel):
    target_date: str
    editorial_note: str
    candidates: List[Candidate]

class ScorePack(BaseModel):
    hook: int = Field(ge=0, le=100)
    curiosity: int = Field(ge=0, le=100)
    payoff: int = Field(ge=0, le=100)
    expertise: int = Field(ge=0, le=100)
    usefulness: int = Field(ge=0, le=100)
    conversation: int = Field(ge=0, le=100)
    shareability: int = Field(ge=0, le=100)
    originality: int = Field(ge=0, le=100)
    total: int = Field(ge=0, le=100)

class PollIdea(BaseModel):
    suitable: bool = False
    question: str = ""
    options: List[str] = []

class ThreadDraft(BaseModel):
    topic: str
    category: Category
    goal: Goal
    sensitivity: Sensitivity
    hooks: List[str] = Field(min_length=5, max_length=10)
    first_lines: List[str] = Field(min_length=2, max_length=5)
    body: str
    closing_line: str
    discussion_questions: List[str] = Field(min_length=2, max_length=5)
    first_reply_options: List[str] = Field(min_length=2, max_length=5)
    source_reply: str = ""
    save_line: str = ""
    share_line: str = ""
    topic_tag: str = ""
    poll: PollIdea = PollIdea()
    fact_check_points: List[str]
    source_refs: List[int] = []
    affiliate_fit: Literal["없음", "약함", "좋음"]
    affiliate_angle: str
    scores: ScorePack
    editor_note: str

class RewriteResult(BaseModel):
    hook: str
    body: str
    closing_line: str
    question: str
    first_reply: str
    editor_note: str

class QualityReview(BaseModel):
    scores: ScorePack
    strengths: List[str]
    fixes: List[str]
    question_is_natural: bool
    clickbait_risk: int = Field(ge=0, le=100)
    revised_hook: str
    revised_body: str
    revised_closing: str
    revised_question: str

class ReplyOption(BaseModel):
    label: str
    text: str
    why: str

class ReplyBundle(BaseModel):
    context_summary: str
    options: List[ReplyOption] = Field(min_length=3, max_length=5)
    avoid: List[str]

class MoneyRoute(BaseModel):
    route: Literal["제휴", "네이버/구글 광고", "자체 PDF·전자책", "유튜브 확장", "브랜드 협업", "검색자산"]
    fit_score: int = Field(ge=0, le=100)
    why: str
    offer_idea: str
    content_bridge: str
    timing: str

class MoneyPlan(BaseModel):
    topic: str
    money_score: int = Field(ge=0, le=100)
    audience_value_score: int = Field(ge=0, le=100)
    best_route: str
    routes: List[MoneyRoute]
    do_not_sell: List[str]
    next_asset: str
    one_line_strategy: str

class PlatformDraft(BaseModel):
    channel: Literal["naver_blog", "adsense_blog", "youtube_shorts", "instagram"]
    title_options: List[str] = Field(min_length=3, max_length=8)
    content: str
    search_keywords: List[str]
    human_value_add: List[str]
    fact_check_points: List[str]
    monetization_note: str

class MultiChannelBundle(BaseModel):
    source_topic: str
    drafts: List[PlatformDraft]

class BenchmarkPattern(BaseModel):
    name: str
    description: str
    why_it_works: str
    use_for_morroway: str
    avoid: str

class Top100Analysis(BaseModel):
    sample_size: int
    caveat: str
    strongest_signals: List[str]
    hook_patterns: List[BenchmarkPattern]
    rhythm_rules: List[str]
    wit_rules: List[str]
    expertise_rules: List[str]
    usefulness_rules: List[str]
    conversation_rules: List[str]
    anti_patterns: List[str]
    generation_brief: str
