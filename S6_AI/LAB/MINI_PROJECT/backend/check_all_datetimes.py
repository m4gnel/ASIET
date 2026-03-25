#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('interview_coach.db')
cursor = conn.cursor()

# Get all columns from all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

print('Checking all DATE/DATETIME columns:')
for table in tables:
    cursor.execute(f'PRAGMA table_info({table})')
    columns = cursor.fetchall()
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        if col_type in ['DATETIME', 'DATE']:
            # Get sample values
            cursor.execute(f'SELECT id, "{col_name}" FROM {table} LIMIT 5')
            rows = cursor.fetchall()
            print(f'\n{table}.{col_name} ({col_type}):')
            for row in rows:
                val = row[1]
                if val and ' ' in str(val) and 'T' not in str(val):
                    print(f'  ID {row[0]}: {repr(val)} ❌ NEEDS FIX')
                else:
                    print(f'  ID {row[0]}: {repr(val)} ✓')

conn.close()
