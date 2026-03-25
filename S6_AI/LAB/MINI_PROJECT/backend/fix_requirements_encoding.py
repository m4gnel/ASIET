"""Fix requirements.txt encoding from UTF-16 to UTF-8"""
import os

path = os.path.join(os.path.dirname(__file__), 'requirements.txt')

# Read the UTF-16 content
with open(path, 'r', encoding='utf-16') as f:
    content = f.read()

# Remove BOM if present
content = content.lstrip('\ufeff')

# Write back as UTF-8
with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("✅ requirements.txt encoding fixed (UTF-16 → UTF-8)")

# Verify
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(f"   {len(lines)} lines, first: {lines[0].strip()}")
