import pathlib
path=pathlib.Path(r'c:\projects\ai_coach_demo_p2\backend\app.py')
text=path.read_text(encoding='utf-8',errors='ignore').splitlines()
for i,line in enumerate(text,1):
    if 'db.create_all()' in line:
        print(i, repr(line))
        if i-2>=1: print('prev:', repr(text[i-2]))
        if i-1>=1: print('prev1:', repr(text[i-1]))
