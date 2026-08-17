from __future__ import annotations
import io, json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).parent
PROFILE_PATH=ROOT/"data"/"benchmarks"/"style_profile.json"
TEXT_COLUMNS=["text","content","post_text","body","caption","thread"]

def read_benchmark_upload(uploaded):
    name=getattr(uploaded,"name","").lower()
    raw=uploaded.getvalue() if hasattr(uploaded,"getvalue") else uploaded.read()
    if name.endswith(".json"):
        obj=json.loads(raw.decode("utf-8")); df=pd.DataFrame(obj if isinstance(obj,list) else obj.get("data",[]))
    else:
        sep="\t" if name.endswith(".tsv") else ","
        df=pd.read_csv(io.BytesIO(raw),sep=sep)
    text_col=next((c for c in TEXT_COLUMNS if c in df.columns),None)
    if not text_col: raise ValueError("text/content/post_text/body/caption/thread 중 본문 열이 필요합니다.")
    out=pd.DataFrame({"text":df[text_col].fillna("").astype(str)})
    for c in ["likes","replies","reposts","views"]:
        out[c]=pd.to_numeric(df[c],errors="coerce").fillna(0) if c in df.columns else 0
    for c in ["url","author"]:
        out[c]=df[c].fillna("").astype(str) if c in df.columns else ""
    out=out[out.text.str.strip().str.len()>0].head(100).copy()
    # 데이터셋 내부 상대 점수. 글로벌 순위가 아님.
    out["benchmark_score"]=(out.likes + out.replies*2.2 + out.reposts*2.7 + out.views*0.03).round(1)
    return out.sort_values("benchmark_score",ascending=False).reset_index(drop=True)

def benchmark_prompt_payload(df:pd.DataFrame):
    rows=[]
    for i,r in df.head(100).iterrows():
        rows.append(f"[{i+1}] likes={int(r.likes)} replies={int(r.replies)} reposts={int(r.reposts)} views={int(r.views)}\n{r.text[:1500]}")
    return "\n\n".join(rows)

def save_style_profile(profile:dict):
    PROFILE_PATH.parent.mkdir(parents=True,exist_ok=True)
    PROFILE_PATH.write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding="utf-8")

def load_style_profile():
    if PROFILE_PATH.exists():
        try: return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception: return None
    return None

def style_profile_brief():
    p=load_style_profile()
    if not p: return "저장된 TOP100 벤치마크 없음. 공식 Threads 성공 원칙과 MORROWAY 기본 문법을 사용한다."
    return p.get("generation_brief") or "저장된 벤치마크의 일반화된 문법만 사용한다."
