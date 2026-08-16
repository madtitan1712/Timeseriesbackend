import glob, os

files = sorted(glob.glob('app/**/*.py', recursive=True) + ['testGeneration.py'])

with open('codebase_summary.txt', 'w') as out:
    for f in files:
        if not os.path.exists(f):
            continue
        out.write(f'=== FILE: {f} ===\n')
        with open(f, encoding='utf-8', errors='replace') as fh:
            out.write(fh.read())
        out.write('\n\n')

print(f'Wrote {len(files)} files to codebase_summary.txt')