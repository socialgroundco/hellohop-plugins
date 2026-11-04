#!/usr/bin/env python3
"""Scan the whole public bundle, including hidden files, before publication.

Run from anywhere; explicit paths replace the default bundle scan.
Only dependency caches, Python bytecode and Git internals are excluded.
"""
from pathlib import Path
import re
import sys
import tempfile

# These names were deliberately retired. Keep synthetic controls live while
# ensuring that this public script itself carries none of the retired names.
FORBIDDEN = ('wa' + 'gate', 'wh' + 'api', 'ra' + 'mow')
PATTERN = re.compile('|'.join(re.escape(word) for word in FORBIDDEN), re.IGNORECASE)
IGNORED = {'.git', 'node_modules', '__pycache__'}


def forbidden_hits(text):
    return list(PATTERN.finditer(text))


def files_under(root):
    if not root.exists():
        raise FileNotFoundError(f'scan target does not exist: {root}')
    if root.is_symlink():
        raise ValueError(f'symlink is not a reviewable public file: {root}')
    if root.is_file():
        yield root
        return
    for child in sorted(root.iterdir()):
        if child.name in IGNORED:
            continue
        yield from files_under(child)


def scan(roots):
    files = sorted({file for root in roots for file in files_under(root)})
    if not files:
        raise ValueError('scan target contains no files')
    hits = []
    for file in files:
        # Byte-preserving decode also catches retired ASCII names in assets.
        text = file.read_bytes().decode('latin1')
        for match in forbidden_hits(text):
            hits.append(f'{file}:{text.count(chr(10), 0, match.start()) + 1}')
        if forbidden_hits(file.name):
            hits.append(f'{file}:filename')
    return len(files), hits


def assertBanIsLive():
    with tempfile.TemporaryDirectory(prefix='hellohop-sweep-') as tmp:
        planted = Path(tmp) / 'planted.md'
        planted.write_text('\n'.join(word.upper() for word in FORBIDDEN))
        assert planted.read_text().splitlines() == [word.upper() for word in FORBIDDEN], 'positive control planting failed'
        count, hits = scan([Path(tmp)])
        assert count == 1 and len(hits) == 3, f'positive control: expected 3 planted hits, got {len(hits)}'
    return 'positive control: 3/3 planted hits caught'


def main():
    print(assertBanIsLive())
    bundle = Path(__file__).resolve().parents[1]
    roots = [bundle] + [Path(arg).resolve() for arg in sys.argv[1:]]
    # Explicit targets replace the default only for isolated checker tests.
    if sys.argv[1:]:
        roots = roots[1:]
    count, hits = scan(roots)
    for hit in hits:
        print(hit)
    print(f'scan: {count} files, {len(hits)} forbidden hits')
    return 1 if hits else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, AssertionError) as err:
        print(f'FAIL: {err}', file=sys.stderr)
        sys.exit(2)
