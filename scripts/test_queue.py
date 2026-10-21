#!/usr/bin/env python3
"""Read-only regression checks. No repository changes."""
import copy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from complete_set import apply,read,validate
def main():
    queue=read("queue.json");progress=read("progress.json");bank=read("lesson-bank.json")
    assert queue["target_pending_sets"]==3
    assert len([s for s in queue["sets"] if s["status"]=="pending"])==3
    assert len(bank["questions"])>=50
    legacy=copy.deepcopy(progress)
    first=queue["sets"][0]
    payload={"set_id":first["set_id"],"attempts":[{"question_id":qid,"attempt_id":"test-attempt-"+str(i).zfill(3),"answer":"計算過程","status":["×","△","○","△","○"][i]} for i,qid in enumerate(first["question_ids"])]}
    q,p=copy.deepcopy(queue),copy.deepcopy(progress)
    assert apply(payload,q,bank,p)
    assert len([s for s in q["sets"] if s["status"] in ("pending","ready")])==3
    assert len(q["sets"][-1]["question_ids"])==5
    assert p["total_questions"]==legacy["total_questions"]+5
    assert p["history"][:len(legacy["history"])]==legacy["history"]
    assert not apply(payload,q,bank,p),"Replay must be no-op"
    invalid=copy.deepcopy(payload)
    invalid["attempts"][0]["answer"]=""
    try:
        validate(invalid,queue,bank,progress)
        raise AssertionError("Blank answer was incorrectly accepted")
    except ValueError:pass
    print("PASS: preserve 50+, legacy history, valid five grades, refill to three, exact replay no-op, reject blank answers")
if __name__=="__main__":main()
