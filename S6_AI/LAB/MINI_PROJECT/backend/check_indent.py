import itertools
with open(r'c:\projects\ai_coach_demo_p2\backend\app.py','r',encoding='utf-8',errors='ignore') as f:
    for i,line in enumerate(f,1):
        if 1010<=i<=1022:
            print(i, repr(line))
