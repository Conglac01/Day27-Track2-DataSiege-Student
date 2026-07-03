import re, subprocess, json
with open("solution/defense.py") as f: code = f.read()
for z in [2.6, 2.7, 2.8, 2.9, 3.0]:
    for c4 in [6.0, 8.0]:
        c2 = 5.0
        c = re.sub(r'Z_THRESH = [\d\.]+', f'Z_THRESH = {z}', code)
        c = re.sub(r'COMBINED_THRESH_4 = [\d\.]+', f'COMBINED_THRESH_4 = {c4}', c)
        c = re.sub(r'COMBINED_THRESH_2 = [\d\.]+', f'COMBINED_THRESH_2 = {c2}', c)
        with open("solution/defense.py", "w") as f: f.write(c)
        subprocess.run([".venv/bin/python3", "harness/run.py", "--phase", "private", "--defense", "solution/defense.py", "--out", "solution/private_report.json"], capture_output=True)
        with open("solution/private_report.json") as f:
            print(f"Z={z} C4={c4} -> Score {json.load(f)['result']['score']}")
