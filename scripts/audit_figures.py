import os, sys, json

sys.stdout.reconfigure(encoding='utf-8')
p = os.path.expanduser(r'~/.exam_generator/figures')
idx_path = os.path.join(p, 'index.json')

with open(idx_path, 'r', encoding='utf-8-sig') as f:
    entries = json.load(f)

print(f"Checking {len(entries)} entries in bank...")

issues = []
valid = 0
for entry in entries:
    fid = entry.get('id')
    tex_path = os.path.join(p, f'figure_{fid}.tex')
    png_path = os.path.join(p, f'figure_{fid}.png')
    
    if not os.path.exists(tex_path):
        issues.append((fid, 'Missing .tex file', entry.get('title', '')))
        continue
    if not os.path.exists(png_path) or os.path.getsize(png_path) == 0:
        issues.append((fid, 'Missing or empty .png', entry.get('title', '')))
        
    with open(tex_path, 'r', encoding='utf-8', errors='ignore') as tf:
        content = tf.read().strip()
        
    if not content:
        issues.append((fid, 'Empty .tex content', entry.get('title', '')))
    elif '\\begin{tikzpicture}' not in content and '\\draw' not in content and '\\tkzTab' not in content:
        issues.append((fid, 'Invalid TikZ structure (no begin/draw/tkzTab)', entry.get('title', '')))
    elif content.count('{') != content.count('}'):
        issues.append((fid, f"Brace mismatch: {content.count('{')} vs {content.count('}')}", entry.get('title', '')))
    else:
        valid += 1

print(f"Valid figures: {valid}, Problematic figures: {len(issues)}")
for fid, issue, title in issues[:40]:
    print(f"  Figure #{fid} ({title}): {issue}")
