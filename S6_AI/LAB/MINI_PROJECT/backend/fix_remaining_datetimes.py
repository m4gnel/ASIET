#!/usr/bin/env python3
"""Fix remaining corrupted datetime values"""
import sqlite3
from datetime import datetime

def fix_datetime_string(dt_str, is_date=False):
    """Convert datetime string to proper format for SQLAlchemy"""
    if not dt_str:
        return None
    
    dt_str = str(dt_str).strip()
    
    # If it already has 'T', it's likely fine for DATETIME columns
    if 'T' in dt_str:
        if is_date:
            # Extract just the date part
            return dt_str.split('T')[0]
        return dt_str
    
    # If it has space-separated format, convert it
    if ' ' in dt_str and '-' in dt_str:
        try:
            # Parse and convert
            dt = datetime.fromisoformat(dt_str.replace(' ', 'T'))
            if is_date:
                return dt.date().isoformat()
            return dt.isoformat()
        except:
            return None
    
    return dt_str if not is_date else dt_str[:10] if len(dt_str) >= 10 else dt_str

conn = sqlite3.connect('interview_coach.db')
cursor = conn.cursor()

print("=== Fixing remaining corrupted datetime values ===\n")

# Table fixes with column info
fixes = [
    ('users', [('last_activity_date', True)]),  # (table, [(column, is_date)])
    ('question_bank', [('created_at', False)]),
    ('feedback', [('generated_at', False)]),
]

for table, columns in fixes:
    print(f"Fixing {table}...")
    
    for col, is_date in columns:
        # Check if table/column exists
        try:
            cursor.execute(f'SELECT count(*) FROM {table}')
        except:
            print(f"  ⚠ Table {table} not found, skipping")
            continue
        
        # Get all rows
        cursor.execute(f'SELECT id, "{col}" FROM {table} WHERE "{col}" IS NOT NULL')
        rows = cursor.fetchall()
        
        if not rows:
            print(f"  ✓ {col}: no data to fix")
            continue
        
        # Check which ones need fixing
        needs_fix = []
        for row_id, val in rows:
            val_str = str(val)
            if ' ' in val_str and ('T' not in val_str or (is_date and ' ' in val_str)):
                needs_fix.append((row_id, val_str))
        
        if not needs_fix:
            print(f"  ✓ {col}: all values already correct")
            continue
        
        # Fix them
        print(f"  Fixing {col} ({len(needs_fix)} rows)...")
        for row_id, old_val in needs_fix:
            new_val = fix_datetime_string(old_val, is_date)
            if new_val:
                cursor.execute(f'UPDATE {table} SET "{col}" = ? WHERE id = ?',
                              (new_val, row_id))
                print(f"    {row_id}: {old_val} → {new_val}")
            else:
                # Set to NULL if we can't fix it
                cursor.execute(f'UPDATE {table} SET "{col}" = NULL WHERE id = ?', (row_id,))
                print(f"    {row_id}: {old_val} → NULL (unparseable)")
        
        conn.commit()
        print(f"  ✓ Fixed {col}")

print("\n=== Fix complete! ===")
conn.close()
