#!/usr/bin/env python3
"""Apply externally graded answers, then refill 3 active sets without a server.
Never grades answers. Commit and push the resulting files together with git.
Usage: python scripts/complete_set.py grades.json --dry-run
       python scripts/complete_set.py grades.json --commit
grades.json: {"set_id":"S0001","attempts":[{"question_id":"Q001","attempt_id":"uuid","answer":"...","status":"○"}, ...]}
"""
import argparse,json,subprocess,sys
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1]
JST=timezone(timedelta(hours=9))
GRADES={"○","△","×"}
def read(name):return json.loads((ROOT/"data"/name).read_text(encoding="utf-8"))
def validate(payload,queue,bank,progress):
    sid=payload["set_id"]
    sets=queue["sets"]
    current=next((s for s in sets if s["set_id"]==sid),None)
    if not current:raise ValueError("Set does not exist")
    if current["status"]=="consumed":
        prior={x.get("attempt_id") for x in progress["history"]}
        requested={x["attempt_id"] for x in payload["attempts"]}
        if requested.issubset(prior):return None # idempotent replay
        raise ValueError("Already consumed with different attempts")
    if current["status"] not in ("pending","ready"):raise ValueError("Not active")
    attempts=payload["attempts"]
    if len(attempts)!=5 or set(a["question_id"] for a in attempts)!=set(current["question_ids"]):raise ValueError("Must grade exactly all five set questions")
    existing={h.get("attempt_id") for h in progress["history"] if h.get("attempt_id")}
    attempt_ids=[a.get("attempt_id") for a in attempts]
    if any(not isinstance(x,str) or len(x)<8 for x in attempt_ids) or len(set(attempt_ids))!=5 or set(attempt_ids)&existing:raise ValueError("Duplicate or missing attempt_id")
    if any(a.get("status") not in GRADES or not str(a.get("answer","")).strip() for a in attempts):raise ValueError("Missing grade or answer; ungraded questions cannot be consumed")
    return current
def refill(queue,bank,progress,current):
    enrolled={qid for s in queue["sets"] if s["status"] in ("pending","ready","consumed") for qid in s["question_ids"]}
    questions=bank["questions"];byid={q["id"]:q for q in questions}
    new=[q["id"] for q in questions if q["id"] not in enrolled]
    latest={t["id"]:t.get("status","未確認") for t in progress["topics"]}
    for h in progress["history"]:
        if h.get("status") in GRADES:latest[h.get("topic_id")]=h["status"]
    known=[qid for qid in enrolled if qid in byid and latest.get(byid[qid]["topic_id"]) in GRADES]
    priority={"×":0,"△":1,"○":2}
    known.sort(key=lambda qid:(priority[latest[byid[qid]["topic_id"]]],qid))
    active={qid for s in queue["sets"] if s["status"] in ("pending","ready") for qid in s["question_ids"] if s is not current}
    reviews=[qid for qid in known if qid not in active][:2]
    needed=5-len(reviews)
    new=[qid for qid in new if qid not in active][:needed]
    if len(new)+len(reviews)<5:raise ValueError("Insufficient validated question pool; add new questions to SQLite, run build, then retry")
    ids=new+reviews
    sequence=max(s["sequence"] for s in queue["sets"])+1
    sid="S"+str(sequence).zfill(4)
    timestamp=datetime.now(JST).isoformat()
    return {"set_id":sid,"sequence":sequence,"status":"pending","origin":"refill_existing_question_bank","generated_at":None,"enqueued_at":timestamp,"consumed_at":None,"question_ids":ids,"graded_question_ids":[],"consumption_id":None}
def apply(payload,queue,bank,progress):
    current=validate(payload,queue,bank,progress)
    if current is None:return False
    now=datetime.now(JST)
    old_attempts={h.get("question_id") for h in progress["history"] if h.get("attempt_id")}
    legacy_ids={h.get("question_id") for h in progress["history"] if h.get("question_id")}
    byid={q["id"]:q for q in bank["questions"]}
    for a in payload["attempts"]:
        q=byid[a["question_id"]]
        # Q001-format new IDs do not collide with pre-Queue numeric legacy IDs
        first_time=a["question_id"] not in old_attempts and a["question_id"] not in legacy_ids
        if first_time:
            progress["total_questions"]+=1
            progress["counts"][a["status"]]+=1
        else:
            former=next((h["status"] for h in reversed(progress["history"]) if h.get("question_id")==a["question_id"] and h.get("status") in GRADES),None)
            if former and former!=a["status"]:
                progress["counts"][former]-=1
                progress["counts"][a["status"]]+=1
        progress["history"].append({"attempt_id":a["attempt_id"],"question_id":a["question_id"],"topic_id":q["topic_id"],"set_id":payload["set_id"],"status":a["status"],"answer":a["answer"],"date":now.date().isoformat(),"answered_at":now.isoformat()})
        old_attempts.add(a["question_id"])
        progress["topics"][next(i for i,t in enumerate(progress["topics"]) if t["id"]==q["topic_id"])]["status"]=a["status"]
    progress["updated_at"]=now.isoformat()
    addition=refill(queue,bank,progress,current)
    current["status"]="consumed"
    current["graded_question_ids"]=[a["question_id"] for a in payload["attempts"]]
    current["consumed_at"]=now.isoformat()
    current["consumption_id"]="consume:"+payload["set_id"]+":"+sorted(a["attempt_id"] for a in payload["attempts"])[0]
    queue["sets"].append(addition)
    queue["updated_at"]=now.isoformat()
    assert len([s for s in queue["sets"] if s["status"] in ("pending","ready")])==queue["target_pending_sets"]==3
    return True
def main():
    p=argparse.ArgumentParser()
    p.add_argument("grades",type=Path)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run",action="store_true")
    mode.add_argument("--commit",action="store_true")
    a=p.parse_args()
    if a.commit:
        subprocess.run(["git","diff","--quiet"],cwd=ROOT,check=True)
        subprocess.run(["git","diff","--cached","--quiet"],cwd=ROOT,check=True)
        subprocess.run(["git","fetch","origin","main"],cwd=ROOT,check=True)
        local=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
        remote=subprocess.check_output(["git","rev-parse","origin/main"],cwd=ROOT,text=True).strip()
        if local!=remote:raise SystemExit("Remote HEAD changed, retry from latest checkout")
    payload=json.loads(a.grades.read_text(encoding="utf-8"))
    queue,bank,progress=read("queue.json"),read("lesson-bank.json"),read("progress.json")
    changed=apply(payload,queue,bank,progress)
    if not changed:print("Already consumed; identical attempts: no-op");return
    if a.dry_run:
        print(json.dumps({"next_set":queue["sets"][-1],"total_questions":progress["total_questions"],"active":3},ensure_ascii=False,indent=2))
        return
    for name,obj in [("queue.json",queue),("progress.json",progress)]:
        (ROOT/"data"/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    subprocess.run(["git","add","data/queue.json","data/progress.json"],cwd=ROOT,check=True)
    subprocess.run(["git","commit","-m","Grade and refill "+payload["set_id"]],cwd=ROOT,check=True)
    subprocess.run(["git","push","origin","HEAD:main"],cwd=ROOT,check=True)
    print("Published graded attempts and refilled queue in ONE commit")
if __name__=="__main__":main()
