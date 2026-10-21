#!/usr/bin/env python3
"""SQLite curriculum master. progress.json and queue.json are NOT SQLite-owned."""
import argparse
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = DATA / "curriculum.sqlite3"
def read(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))
def write(name, value):
    (DATA / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def connect():
    db = sqlite3.connect(DB)
    db.execute("PRAGMA foreign_keys=ON")
    return db
def schema(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, json_value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS topics (
        topic_id TEXT PRIMARY KEY, name TEXT NOT NULL, domain TEXT NOT NULL,
        parent_id TEXT REFERENCES topics(topic_id), payload_json TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS lectures (
        topic_id TEXT PRIMARY KEY REFERENCES topics(topic_id),
        intuition TEXT NOT NULL, definition TEXT NOT NULL,
        derivation TEXT NOT NULL, example TEXT NOT NULL,
        conditions TEXT NOT NULL, pitfalls TEXT NOT NULL,
        exam_criteria TEXT NOT NULL, review_status TEXT NOT NULL
            CHECK(review_status IN ('draft','in_review','approved','needs_revision')),
        review_notes TEXT NOT NULL DEFAULT '',
        revised_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS questions (
        question_id TEXT PRIMARY KEY, topic_id TEXT NOT NULL REFERENCES topics(topic_id),
        payload_json TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS legacy_sets (
        day INTEGER PRIMARY KEY, question_ids_json TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic_id);
    """)
def init(force=False):
    if DB.exists():
        if not force:
            print("Existing SQLite master retained; use build to export JSON.")
            return
        raise SystemExit("Refusing destructive rebuild of the SQLite master")
    taxonomy, bank, progress = read("taxonomy.json"), read("lesson-bank.json"), read("progress.json")
    seed = json.loads((ROOT / "scripts" / "lecture_seed.json").read_text(encoding="utf-8"))
    topics = {t["id"]: t for t in progress["topics"]}
    assert len(topics) == 239 and len(bank["questions"]) == 50
    assert set(taxonomy["learning_unit_ids"]).issubset(topics)
    db=connect()
    with db:
        schema(db)
        db.execute("INSERT INTO metadata VALUES (?,?)",("taxonomy",json.dumps(taxonomy,ensure_ascii=False)))
        db.execute("INSERT INTO metadata VALUES (?,?)",("bank_header",json.dumps({k:v for k,v in bank.items() if k not in ("questions","days")},ensure_ascii=False)))
        for tid,t in topics.items():
            db.execute("INSERT INTO topics(topic_id,name,domain,parent_id,payload_json) VALUES(?,?,?,?,?)",
                (tid,t["name"],t["domain"],None,json.dumps(t,ensure_ascii=False)))
        for child,parent in taxonomy["parent_by_child"].items():
            db.execute("UPDATE topics SET parent_id=? WHERE topic_id=?",(parent,child))
        question_topics = {}
        for q in bank["questions"]:
            db.execute("INSERT INTO questions VALUES (?,?,?)",(q["id"],q["topic_id"],json.dumps(q,ensure_ascii=False)))
            question_topics.setdefault(q["topic_id"],q)
        for day in bank["days"]:
            db.execute("INSERT INTO legacy_sets VALUES (?,?)",(day["day"],json.dumps(day["question_ids"])))
        for tid,t in topics.items():
            q = question_topics.get(tid)
            s = seed.get(tid)
            if s:
                fields=[s[x] for x in ("intuition","definition","derivation","example","conditions","pitfalls","exam_criteria")]
                state=s["review_status"]; notes=s["review_notes"]
            else:
                fields=[(q or {}).get("lecture",""),"","","","",(q or {}).get("pitfall",""),""]
                state="needs_revision"; notes="体系的な初回講義は未作成。旧ミニ講義がある場合は暫定掲載。"
            db.execute("INSERT INTO lectures VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (tid,*fields,state,notes,datetime.now(timezone.utc).isoformat()))
    db.close()
    print(f"Initialized SQLite master: {DB} (topics={len(topics)}, questions=50, structured_lectures={len(seed)})")
def build():
    if not DB.exists(): raise SystemExit("Missing curriculum.sqlite3: run init first")
    db=connect()
    result=db.execute("PRAGMA integrity_check").fetchone()[0]
    assert result=="ok",result
    t=json.loads(db.execute("SELECT json_value FROM metadata WHERE key='taxonomy'").fetchone()[0])
    header=json.loads(db.execute("SELECT json_value FROM metadata WHERE key='bank_header'").fetchone()[0])
    questions=[json.loads(row[0]) for row in db.execute("SELECT payload_json FROM questions ORDER BY question_id")]
    for q in questions:
        q["lecture_id"]=q["topic_id"]
    header["days"]=[{"day":d,"question_ids":json.loads(j)} for d,j in db.execute("SELECT day,question_ids_json FROM legacy_sets ORDER BY day")]
    header["questions"]=questions
    lectures={}
    for row in db.execute("SELECT topic_id,intuition,definition,derivation,example,conditions,pitfalls,exam_criteria,review_status,review_notes,revised_at FROM lectures ORDER BY topic_id"):
        tid,*rest=row
        lectures[tid]=dict(zip(("intuition","definition","derivation","example","conditions","pitfalls","exam_criteria","review_status","review_notes","revised_at"),rest))
    # Reuse canonical formula TeX stored with a question in SQLite, without copying lecture body into every question.
    formula_by_topic={}
    for item in questions:
        if item.get("formula_latex") and item["topic_id"] not in formula_by_topic:
            formula_by_topic[item["topic_id"]]=item["formula_latex"]
    for topic_id,lecture in lectures.items():
        lecture["formula_latex"]=formula_by_topic.get(topic_id,"")
    # Validate all exported references and preserve immutable question IDs.
    ids={r[0] for r in db.execute("SELECT topic_id FROM topics")}
    assert len(questions)==len({q["id"] for q in questions})
    assert all(q["topic_id"] in ids and q["lecture_id"] in lectures for q in questions)
    assert len(t["learning_unit_ids"])==t["learning_unit_count"]
    write("taxonomy.json",t)
    write("lesson-bank.json",header)
    write("lectures.json",{"schema_version":1,"source":"data/curriculum.sqlite3","lectures":lectures})
    db.close()
    print(f"Built public JSON: {len(questions)} questions, {len(lectures)} lectures")
def verify():
    db=connect()
    assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    assert db.execute("PRAGMA foreign_key_check").fetchall()==[]
    bank=read("lesson-bank.json"); lectures=read("lectures.json")["lectures"]; queue=read("queue.json"); progress=read("progress.json")
    assert len(bank["questions"])>=50 and len({q["id"] for q in bank["questions"]})==len(bank["questions"])
    assert all(q["lecture_id"] in lectures for q in bank["questions"])
    active=[s for s in queue["sets"] if s["status"] in ("pending","ready")]
    assert queue["target_pending_sets"]==3 and len(active)==3
    assert all(len(s["question_ids"])==5 for s in active)
    ids={q["id"] for q in bank["questions"]}
    assert all(set(s["question_ids"]).issubset(ids) for s in queue["sets"])
    migrated=db.execute("SELECT json_value FROM metadata WHERE key='lecture_math_v1'").fetchone()
    if migrated:
        for tid in json.loads(migrated[0])["topics"]:
            entry=lectures[tid]
            assert entry["review_status"]=="draft" or entry["review_status"] in ("in_review","approved","needs_revision")
            assert any("\\(" in entry[field] and "\\)" in entry[field] for field in ("definition","derivation","example")), ("Missing KaTeX delimiters",tid)
        assert isinstance(progress.get("history"), list) and isinstance(progress.get("total_questions"), int), "Invalid progress schema"
    print(f"OK: sqlite, JSON references, active queue={len(active)}, legacy history={len(progress['history'])}")
    db.close()
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=("init","build","verify"))
    args=parser.parse_args()
    globals()[args.command]()
