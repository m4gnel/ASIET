#!/usr/bin/env python3
"""Fix corrupted datetime values in the database"""
import sqlite3
from datetime import datetime

def fix_datetime_string(dt_str):
    """Convert datetime string with spaces to ISO format with T"""
    if not dt_str:
        return dt_str
    
    # If it already has 'T', it's fine
    if 'T' in dt_str:
        return dt_str
    
    # If it has space-separated format, convert it
    if ' ' in dt_str and '-' in dt_str:
        try:
            # Parse the space-separated format and re-serialize with 'T'
            dt = datetime.fromisoformat(dt_str.replace(' ', 'T'))
            return dt.isoformat()
        except:
            return dt_str
    
    return dt_str

# Connect to database
conn = sqlite3.connect('interview_coach.db')
cursor = conn.cursor()

print("=== Fixing datetime values in database ===\n")

# Tables with datetime columns
datetime_fixes = [
    ('users', ['created_at', 'last_login']),
    ('interviews', ['started_at', 'completed_at']),
    ('questions', ['created_at']),
    ('answers', ['submitted_at']),
    ('feedbacks', ['generated_at']),
    ('question_banks', ['created_at']),
]

for table, datetime_columns in datetime_fixes:
    for col in datetime_columns:
        print(f"Checking {table}.{col}...")
        
        # Get all rows with data in this column
        cursor.execute(f'SELECT id, {col} FROM {table} WHERE {col} IS NOT NULL')
        rows = cursor.fetchall()
        
        if not rows:
            print(f"  ✓ No data to fix")
            continue
        
        # Check if any need fixing
        needs_fix = []
        for row_id, dt_value in rows:
            if dt_value and ' ' in dt_value and 'T' not in dt_value:
                needs_fix.append((row_id, dt_value))
        
        if not needs_fix:
            print(f"  ✓ All values already in correct format")
            continue
        
        print(f"  Found {len(needs_fix)} values to fix...")
        
        # Fix them
        for row_id, old_value in needs_fix:
            new_value = fix_datetime_string(old_value)
            cursor.execute(f'UPDATE {table} SET {col} = ? WHERE id = ?',
                          (new_value, row_id))
            print(f"    Fixed ID {row_id}: {old_value} → {new_value}")
        
        conn.commit()
        print(f"  ✓ Fixed {len(needs_fix)} rows")

print("\n=== Fix complete! ===")
conn.close()
