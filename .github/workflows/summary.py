"""
Print summary of all pytest results (saved to JSON files).
Without arguments -- ANSI-colored terminal,
with "md" argument -- Markdown,
with "msg" argument -- GitHub notice/warning message (only for skip/warn).
"""
import sys
from glob import glob
import json
from re import findall

# output type
if len(sys.argv) > 1:
    out = sys.argv[1]
else:
    out = 'term'


# formatter for ANSI/Markdown
def fmt(val, cond, style):  # style: 'ok'/'warn'/'err'
    if not cond:
        return val
    if out == 'md':
        val = val.strip()
        if style in ['ok', 'err']:
            return '**' + val + '**'  # bold
        else:
            return '*' + val + '*'  # italic
    if style == 'ok':
        return f'\x1B[32m{val}\x1B[0m'  # green
    elif style == 'err':
        return f'\x1B[31m{val}\x1B[0m'  # red
    else:
        return f'\x1B[33m{val}\x1B[0m'  # yellow


# table header
if out == 'md':
    print('| Testing | Pass | Error | Fail | Warn | Skip |')
    print('| --- | --- | --- | --- | --- | --- |')
    sep = ' | '
elif out == 'term':
    print('Testing  Pass  Error  Fail  Warn  Skip')
    print('======================================')
    sep = '  '

# count runs
good, bad = 0, 0

for fname in sorted(glob('*.json')):
    with open(fname, 'rt') as f:
        res = json.load(f)
    T, E, F, W, S = map(lambda k: int(res[k]),
                        ['tests', 'error', 'failed', 'warnings', 'skipped'])
    P = T - E - F - S  # "pass"
    if 'no-cython' in fname:
        T -= S  # ignore skipped Cython
    ok = P == T

    if out == 'msg':
        if W:
            print(f'::warning::{W} warning{"s" if W > 1 else ""}')
        if S:
            print(f'::{"notice" if ok else "warning"}::{S} skipped')
    else:
        row = sep.lstrip()
        row += fname[:-5]
        if out != 'md':
            row += '\n' + ' ' * len('Testing')
        row += sep + fmt(f'{P:4}', P == T, 'ok')
        row += sep + fmt(f'{E:5}', E, 'err')
        row += sep + fmt(f'{F:4}', F, 'err')
        row += sep + fmt(f'{W:4}', W, 'warn')
        row += sep + fmt(f'{S:4}', S, 'warn' if ok else 'err')
        row += sep.rstrip()
        print(row)
        if ok:
            good += 1
        else:
            bad += 1

# table footer and run counts
if out != 'msg':
    print('' if out == 'md' else '======================================')
    tot = fmt(f'{good} good', not bad, 'ok')
    if bad:
        tot += ', ' + fmt(f'{bad} bad', True, 'err')
    print(tot)
