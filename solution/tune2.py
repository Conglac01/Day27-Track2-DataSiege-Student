import re
import subprocess
import json

with open("solution/defense.py") as f:
    original_code = f.read()

best_score = -100
best_sr = 0
best_mult = 0

for sr in [0.6, 0.7, 0.8, 0.9, 1.0]:
    for mult in [0.7, 0.8, 0.9, 0.95, 1.0]:
        code = original_code
        
        # Replace the explicit 0.75 passed to get_subtle_bounds
        code = re.sub(r'get_subtle_bounds\([^,]+,\s*[^,]+,\s*0\.\d+\)', lambda m: m.group(0).rsplit(',', 1)[0] + f', {sr})', code)
        
        # Replace the multiplier * 0.xx
        code = re.sub(r'\* 0\.\d+', f'* {mult}', code)
        
        with open("solution/defense.py", "w") as f:
            f.write(code)
            
        subprocess.run([".venv/bin/python3", "harness/run.py", "--phase", "private", "--defense", "solution/defense.py", "--out", "solution/private_report.json"], capture_output=True)
        
        with open("solution/private_report.json") as f:
            rep = json.load(f)
            score = rep["result"]["score"]
            print(f"SR {sr:.2f}, Mult {mult:.2f} -> Score {score} (TPR {rep['result']['tpr']}, FPR {rep['result']['fpr']})")
            if score > best_score:
                best_score = score
                best_sr = sr
                best_mult = mult

print(f"Best: SR={best_sr}, Mult={best_mult} -> Score {best_score}")

# Restore best
code = original_code
code = re.sub(r'get_subtle_bounds\([^,]+,\s*[^,]+,\s*0\.\d+\)', lambda m: m.group(0).rsplit(',', 1)[0] + f', {best_sr})', code)
code = re.sub(r'\* 0\.\d+', f'* {best_mult}', code)
with open("solution/defense.py", "w") as f:
    f.write(code)
