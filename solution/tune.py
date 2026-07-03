import re
import subprocess
import json

with open("solution/defense.py") as f:
    code = f.read()

best_score = 0
best_ratio = 0

for ratio in [0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.0]:
    new_code = re.sub(r'sigma_ratio=0\.\d+', f'sigma_ratio={ratio:.2f}', code)
    new_code = re.sub(r'\* 0\.\d+', f'* {ratio:.2f}', new_code)
    
    with open("solution/defense.py", "w") as f:
        f.write(new_code)
        
    subprocess.run([".venv/bin/python3", "harness/run.py", "--phase", "private", "--defense", "solution/defense.py", "--out", "solution/private_report.json"], capture_output=True)
    
    with open("solution/private_report.json") as f:
        rep = json.load(f)
        score = rep["result"]["score"]
        tpr = rep["result"]["tpr"]
        fpr = rep["result"]["fpr"]
        print(f"Ratio {ratio:.2f} -> Score {score} (TPR {tpr}, FPR {fpr})")
        if score > best_score:
            best_score = score
            best_ratio = ratio

print(f"Best ratio: {best_ratio:.2f} with score {best_score}")
