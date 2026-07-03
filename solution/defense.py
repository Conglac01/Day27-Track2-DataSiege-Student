"""
Your defense. Implement register(ctx) and a handler per event type.
See ../README.md for the full interface + toolkit reference, and
../RULES.md before you start.
"""
from api import Verdict

import math

Z_THRESH = 3.0
COMBINED_THRESH_4 = 8.0 # Chi-square 4-DOF: 95% is 9.49, 99% is 13.28
COMBINED_THRESH_2 = 5.0  # Chi-square 2-DOF: 95% is 5.99, 99% is 9.21

def get_z(val, min_val, max_val):
    mean = (min_val + max_val) / 2.0
    std = (max_val - min_val) / 6.0
    return abs(val - mean) / std

def get_z_max(val, max_val):
    std = max_val / 3.0
    return val / std

def check_z(val, min_val, max_val):
    return get_z(val, min_val, max_val) > Z_THRESH

def check_z_max(val, max_val):
    return get_z_max(val, max_val) > Z_THRESH

def register(ctx):
    ctx.on("data_batch", check_data_batch)
    ctx.on("contract_checkpoint", check_contract_checkpoint)
    ctx.on("lineage_run", check_lineage_run)
    ctx.on("feature_materialization", check_feature_materialization)
    ctx.on("embedding_batch", check_embedding_batch)


def check_data_batch(payload, ctx):
    res = ctx.tools.batch_profile(payload["batch_id"])
    if "error" in res:
        return Verdict(alert=False, pillar="checks")
    
    b = ctx.baseline
    alert = False
    reasons = []
    
    z_rc = get_z(res["row_count"], b["row_count_min"], b["row_count_max"])
    z_null = get_z_max(res["null_rate"]["customer_id"], b["null_rate_max"])
    z_ma = get_z(res["mean_amount"], b["mean_amount_min"], b["mean_amount_max"])
    z_stale = get_z_max(res["staleness_min"], b["staleness_min_max"])
    
    ss_z = z_rc**2 + z_null**2 + z_ma**2 + z_stale**2
    
    if ss_z > COMBINED_THRESH_4 or max(z_rc, z_null, z_ma, z_stale) > Z_THRESH:
        alert = True
        reasons.append("combined_anomaly")
        
    return Verdict(alert=alert, pillar="checks", reason=",".join(reasons))


def check_contract_checkpoint(payload, ctx):
    res = ctx.tools.contract_diff(payload["contract_id"], payload["checkpoint_batch_id"])
    if "error" in res:
        return Verdict(alert=False, pillar="contracts")
        
    b = ctx.baseline
    alert = False
    reasons = []
    
    if len(res["violations"]) > 0:
        alert = True; reasons.append("violations")
    if check_z_max(res["freshness_delay_min"], b["freshness_delay_max_min"]):
        alert = True; reasons.append("freshness_delay_min")
        
    return Verdict(alert=alert, pillar="contracts", reason=",".join(reasons))


def check_lineage_run(payload, ctx):
    res = ctx.tools.lineage_graph_slice(payload["run_id"])
    if "error" in res:
        return Verdict(alert=False, pillar="lineage")
        
    b = ctx.baseline
    alert = False
    reasons = []
    
    if check_z_max(res["duration_ms"], b["lineage_duration_ms_max"]):
        alert = True; reasons.append("duration_ms")
        
    job_name = payload["run_id"].rsplit("-", 1)[0]
    
    state_key_up = f"lineage_up_{job_name}"
    actual_up = set(res["actual_upstream"])
    
    if state_key_up not in ctx.state:
        ctx.state[state_key_up] = actual_up
    else:
        if not ctx.state[state_key_up].issubset(actual_up):
            alert = True; reasons.append("missing_upstream")
        ctx.state[state_key_up].update(actual_up)
        
    state_key_down = f"lineage_down_max_{job_name}"
    actual_down = res["actual_downstream_count"]
    
    if state_key_down not in ctx.state:
        ctx.state[state_key_down] = actual_down
    else:
        max_down = ctx.state[state_key_down]
        if max_down > 0 and actual_down == 0:
            alert = True; reasons.append("orphan_output")
        if actual_down > max_down:
            ctx.state[state_key_down] = actual_down

    return Verdict(alert=alert, pillar="lineage", reason=",".join(reasons))


def check_feature_materialization(payload, ctx):
    res = ctx.tools.feature_drift(payload["feature_view"], payload["batch_id"])
    if "error" in res:
        return Verdict(alert=False, pillar="ai_infra")
        
    b = ctx.baseline
    alert = False
    reasons = []
    
    if check_z_max(res["mean_shift_sigma"], b["feature_mean_shift_sigma_max"]):
        alert = True; reasons.append("mean_shift_sigma")
        
    return Verdict(alert=alert, pillar="ai_infra", reason=",".join(reasons))


def check_embedding_batch(payload, ctx):
    res = ctx.tools.embedding_drift(payload["corpus"], payload["chunk_batch_id"])
    if "error" in res:
        return Verdict(alert=False, pillar="ai_infra")
        
    b = ctx.baseline
    alert = False
    reasons = []
    
    z_centroid = get_z_max(res["centroid_shift"], b["embedding_centroid_shift_max"])
    z_age = get_z_max(res["avg_doc_age_days"], b["corpus_avg_doc_age_days_max"])
    
    ss_z = z_centroid**2 + z_age**2
    if ss_z > COMBINED_THRESH_2 or max(z_centroid, z_age) > Z_THRESH:
        alert = True; reasons.append("combined_anomaly")
        
    return Verdict(alert=alert, pillar="ai_infra", reason=",".join(reasons))
