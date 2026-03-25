import pathlib
path=pathlib.Path(r'c:\projects\ai_coach_demo_p2\backend\app.py')
lines=path.read_text(encoding='utf-8', errors='ignore').splitlines()
for idx in range(1007, 1035):
    print(f"{idx+1}: {lines[idx]}")
