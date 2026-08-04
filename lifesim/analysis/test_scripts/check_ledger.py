"""Number-ledger gate: every generated table row must appear in main.tex.

Regenerates nothing. Reads thesis/reviews/tables_generated.tex (produced by
gen_tables.py from the frozen artifacts) and verifies that every data row's
numeric content appears in thesis/main.tex, ignoring whitespace, bolding, and
label-column differences. Exits nonzero listing any row whose numbers are not
found -- the scripted stale-value check of the results-audit gate.

    python check_ledger.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TH = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'thesis'))

gen = open(os.path.join(TH, 'reviews', 'tables_generated.tex'), encoding='utf-8').read()
main = open(os.path.join(TH, 'main.tex'), encoding='utf-8').read()
main_flat = re.sub(r'\\textbf{([^}]*)}', r'\1', main)
main_flat = re.sub(r'\s+', ' ', main_flat)


def numbers(row):
    """All numeric tokens in a table row, as strings, in order."""
    return re.findall(r'-?\d+\.?\d*', row.replace('--', ' '))


checked = missing = 0
for block in re.split(r'% ====', gen):
    lines = [l for l in block.splitlines() if '&' in l and r'\\' in l]
    for row in lines:
        nums = numbers(row)
        if len(nums) < 3:
            continue
        checked += 1
        # A row matches if its full numeric sequence occurs within any single
        # 300-char window of the flattened main.tex.
        pat = r'[^0-9]{1,40}'.join(re.escape(n) for n in nums)
        if not re.search(pat, main_flat):
            # Retry without the leading label-ish number (targets like 5.5
            # may be formatted differently in-document)
            pat2 = r'[^0-9]{1,40}'.join(re.escape(n) for n in nums[1:])
            if not re.search(pat2, main_flat):
                missing += 1
                print(f'MISSING: {row.strip()[:100]}')

print(f'\nledger: {checked} generated rows checked, {missing} missing from main.tex')
sys.exit(1 if missing else 0)
