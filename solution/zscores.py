import sys, json
sys.path.insert(0, "harness")
import crypto

with open("data/baselines.json") as f: b = json.load(f)
key = open("phases/practice.key", "rb").read()
enc = open("phases/practice_schedule.json.enc", "rb").read()
sched = crypto.decrypt_schedule(enc, key)

mean_rc = (b["row_count_min"] + b["row_count_max"]) / 2
std_rc = (b["row_count_max"] - b["row_count_min"]) / 6
mean_ma = (b["mean_amount_min"] + b["mean_amount_max"]) / 2
std_ma = (b["mean_amount_max"] - b["mean_amount_min"]) / 6
std_null = b["null_rate_max"] / 3
std_stale = b["staleness_min_max"] / 3

for ev, label in zip(sched["events"], sched["labels"]):
    if ev["type"] == "data_batch":
        gt = next(t["gt"] for t in sched["ground_truth"] if t["type"] == "data_batch" and t["batch_id_or_ref"] == ev["payload"]["batch_id"])
        z_rc = abs(gt["row_count"] - mean_rc) / std_rc
        z_ma = abs(gt["mean_amount"] - mean_ma) / std_ma
        z_null = gt["null_rate_customer_id"] / std_null
        z_stale = gt["staleness_min"] / std_stale
        print(f"Seq {label['seq']} Faulty={label['is_faulty']} tier={label.get('tier')} | z_rc={z_rc:.2f} z_ma={z_ma:.2f} z_null={z_null:.2f} z_stale={z_stale:.2f}")

