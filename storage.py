from __future__ import annotations
import os, sqlite3, uuid
from pathlib import Path
from datetime import datetime
import pandas as pd

ROOT=Path(__file__).parent
DB_PATH=ROOT/"data"/"morroway_mobile.db"
POST_COLUMNS=["id","created_at","target_date","topic","category","goal","selected_hook","final_text","source_count","status"]
METRIC_COLUMNS=["post_id","measured_at","views","likes","replies","reposts","quotes","profile_visits","follows","link_clicks","orders","revenue"]

SCHEMA="""
CREATE TABLE IF NOT EXISTS posts (
 id TEXT PRIMARY KEY, created_at TEXT, target_date TEXT, topic TEXT, category TEXT, goal TEXT,
 selected_hook TEXT, final_text TEXT, source_count INTEGER DEFAULT 0, status TEXT DEFAULT 'ready'
);
CREATE TABLE IF NOT EXISTS metrics (
 id INTEGER PRIMARY KEY AUTOINCREMENT, post_id TEXT, measured_at TEXT, views INTEGER DEFAULT 0,
 likes INTEGER DEFAULT 0, replies INTEGER DEFAULT 0, reposts INTEGER DEFAULT 0, quotes INTEGER DEFAULT 0,
 profile_visits INTEGER DEFAULT 0, follows INTEGER DEFAULT 0, link_clicks INTEGER DEFAULT 0,
 orders INTEGER DEFAULT 0, revenue REAL DEFAULT 0
);
"""

def _conn():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB_PATH); c.executescript(SCHEMA); return c

def _secret(name, default=None):
    try:
        import streamlit as st
        if name in st.secrets: return st.secrets[name]
    except Exception: pass
    return os.getenv(name,default)

def _sheets_configured():
    try:
        import streamlit as st
        return bool(st.secrets.get("GOOGLE_SHEET_ID")) and "gcp_service_account" in st.secrets
    except Exception: return False

def backend_name(): return "Google Sheets" if _sheets_configured() else "로컬 SQLite"

def _sheet():
    import streamlit as st, gspread
    from google.oauth2.service_account import Credentials
    info=dict(st.secrets["gcp_service_account"])
    scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    creds=Credentials.from_service_account_info(info,scopes=scopes)
    gc=gspread.authorize(creds)
    return gc.open_by_key(st.secrets["GOOGLE_SHEET_ID"])

def _ensure_ws(name, headers):
    sh=_sheet()
    try: ws=sh.worksheet(name)
    except Exception: ws=sh.add_worksheet(title=name,rows=1000,cols=max(12,len(headers)))
    existing=ws.row_values(1)
    if not existing: ws.append_row(headers,value_input_option="RAW")
    return ws

def save_post(record:dict):
    record=dict(record)
    record.setdefault("id",uuid.uuid4().hex[:12]); record.setdefault("created_at",datetime.now().isoformat(timespec="seconds")); record.setdefault("status","ready")
    if _sheets_configured():
        ws=_ensure_ws("posts",POST_COLUMNS); ws.append_row([record.get(c,"") for c in POST_COLUMNS],value_input_option="RAW")
    else:
        with _conn() as c:
            c.execute("INSERT OR REPLACE INTO posts (id,created_at,target_date,topic,category,goal,selected_hook,final_text,source_count,status) VALUES (?,?,?,?,?,?,?,?,?,?)",tuple(record.get(x,"") for x in POST_COLUMNS))
    return record["id"]

def save_metrics(post_id, **kw):
    rec={"post_id":post_id,"measured_at":datetime.now().isoformat(timespec="seconds")}
    rec.update({c:kw.get(c,0) for c in METRIC_COLUMNS[2:]})
    if _sheets_configured():
        ws=_ensure_ws("metrics",METRIC_COLUMNS); ws.append_row([rec.get(c,0) for c in METRIC_COLUMNS],value_input_option="RAW")
    else:
        with _conn() as c:
            c.execute("INSERT INTO metrics (post_id,measured_at,views,likes,replies,reposts,quotes,profile_visits,follows,link_clicks,orders,revenue) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",tuple(rec.get(x,0) for x in METRIC_COLUMNS))

def posts_df():
    if _sheets_configured():
        ws=_ensure_ws("posts",POST_COLUMNS); rows=ws.get_all_records(); return pd.DataFrame(rows,columns=POST_COLUMNS)
    with _conn() as c: return pd.read_sql_query("SELECT * FROM posts ORDER BY created_at DESC",c)

def metrics_df():
    if _sheets_configured():
        ws=_ensure_ws("metrics",METRIC_COLUMNS); rows=ws.get_all_records(); return pd.DataFrame(rows,columns=METRIC_COLUMNS)
    with _conn() as c: return pd.read_sql_query("SELECT post_id,measured_at,views,likes,replies,reposts,quotes,profile_visits,follows,link_clicks,orders,revenue FROM metrics ORDER BY measured_at DESC",c)

def performance_df():
    p=posts_df(); m=metrics_df()
    if p.empty: return p
    if m.empty:
        for c in METRIC_COLUMNS[2:]: p[c]=0
        return p
    m=m.copy(); m["measured_at"]=m["measured_at"].astype(str)
    latest=m.sort_values("measured_at").groupby("post_id",as_index=False).tail(1)
    out=p.merge(latest,on="post_id" if "post_id" in p.columns else "id",how="left") if False else p.merge(latest,left_on="id",right_on="post_id",how="left")
    for c in METRIC_COLUMNS[2:]: out[c]=pd.to_numeric(out[c],errors="coerce").fillna(0)
    return out

def export_all():
    return posts_df(), metrics_df()
