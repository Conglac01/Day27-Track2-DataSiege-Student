import json
with open("solution/practice_report.json") as f: report = json.load(f)
with open("phases/practice_answer_key.json") as f: key = json.load(f)
for v, k in zip(report["result"]["verdicts"], key):
    if v["alert"] and not k["is_faulty"]:
        print(f"False Positive at seq {v['seq']}")
    if not v["alert"] and k["is_faulty"]:
        print(f"False Negative at seq {v['seq']}")
