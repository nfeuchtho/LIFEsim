"""Recover the Stage B scan grids from the cluster run logs.

The two-dimensional operating-point scans write only a figure, so the numbers
behind Figures 5.4 and 5.5 would otherwise exist only as colours. Each grid
point does print a header naming its two agnostic parameters followed by either
a located cutoff or a declaration of infeasibility, so the grid is recoverable
from the log verbatim.

    python recover_stageb_grids.py thesis/images/tse/physical \
                                   thesis/reproducibility/stageb_grids.tsv

A cell is written as its cutoff in ph/s/um, or 0 where no positive budget
reaches the mission-time target.
"""
import os
import re
import sys

import numpy as np

HEAD = re.compile(r">> TSE Run No\. (\d+) / (\d+) \((\w+)=([\d.]+)\D*, FoR=(\d+)")
CUT = re.compile(r">> Budget CUTOFF found: (\d+) ph/s")
IMPOSS = re.compile(r">> Impossible to reach MT target")
# A resumed scan replays already-decided points instead of recomputing them, and
# announces them differently. Without this the whole recovered prefix parses as
# missing, which is most of the grid after an interrupted run.
RECOV = re.compile(r">> Recovered from log: ([\d.]+) ph/s")

# Targets are each architecture's own primary operating point, the lowest half
# year above its zero-budget time. Override with the third argument when
# recovering a run made at different ones.
SCANS = [('mag', 'hi', 4.0), ('mag', 'lo', 5.5),
         ('slew', 'hi', 4.0), ('slew', 'lo', 5.5)]
PREFIX = 'stageb6'


def parse(path):
    """Return (param_name, x values, FoR values, grid) for one scan log."""
    txt = open(path, errors='replace').read()
    pts = []
    for m in HEAD.finditer(txt):
        # The verdict is whichever of the two markers appears first after the
        # header; a point that neither locates a cutoff nor reports failure is
        # left as NaN rather than silently counted as zero.
        tail = txt[m.end(): m.end() + 4000]
        # Take whichever verdict marker appears first after the header. A point
        # that carries none of them is left NaN rather than counted as zero.
        cands = [(mm.start(), kind, mm) for kind, mm in
                 (('cut', CUT.search(tail)), ('rec', RECOV.search(tail)),
                  ('imp', IMPOSS.search(tail))) if mm]
        if not cands:
            val = np.nan
        else:
            _, kind, mm = min(cands)
            val = 0.0 if kind == 'imp' else float(mm.group(1))
        pts.append((float(m.group(4)), float(m.group(5)), val))
    if not pts:
        return None
    name = HEAD.search(txt).group(3)
    xs = sorted({p[0] for p in pts})
    ys = sorted({p[1] for p in pts})
    grid = np.full((len(ys), len(xs)), np.nan)
    for x, y, v in pts:
        grid[ys.index(y), xs.index(x)] = v
    return name, xs, ys, grid


def main(logdir, out):
    rows = ['catalog\tscan\ttarget_yr\tparam\tparam_value\tfor_deg\tbudget_ph_s_um']
    for scan, cat, target in SCANS:
        path = os.path.join(logdir, f'{PREFIX}_{scan}_{cat}.log')
        got = parse(path)
        if got is None:
            print(f'  {os.path.basename(path)}: no grid points', file=sys.stderr)
            continue
        name, xs, ys, grid = got
        for j, x in enumerate(xs):
            for i, y in enumerate(ys):
                v = grid[i, j]
                cell = 'nan' if not np.isfinite(v) else f'{v:.0f}'
                rows.append(f'hab2{cat}\t{scan}\t{target}\t{name}\t{x:g}\t{y:g}\t{cell}')

        feas = np.isfinite(grid) & (grid > 0)
        # Lowest field of regard that still admits a positive budget anywhere,
        # and the spread along each axis at the adopted operating point.
        anyfeas = np.where(feas.any(axis=1))[0]
        edge = ys[anyfeas.min()] if len(anyfeas) else None
        i65 = min(range(len(ys)), key=lambda k: abs(ys[k] - 65))
        adopt = 7.0 if name == 'M' else 12.0
        jad = min(range(len(xs)), key=lambda k: abs(xs[k] - adopt))
        along_x = grid[i65][feas[i65]]
        along_y = grid[:, jad][feas[:, jad]]
        print(f'{cat} {scan}: feasible {feas.sum()}/{grid.size} '
              f'({100 * feas.sum() / grid.size:.1f}%), peak {np.nanmax(grid):.0f}, '
              f'lowest feasible FoR {edge}deg, '
              f'{name} spread at FoR 65 {span(along_x)}, '
              f'FoR spread at {name}={xs[jad]:g} {span(along_y)}')

    with open(out, 'w') as fh:
        fh.write('\n'.join(rows) + '\n')
    print(f'wrote {len(rows) - 1} cells to {out}')


def span(a):
    return f'{a.min():.0f}-{a.max():.0f} ({a.max() / max(a.min(), 1e-9):.2f}x)' if len(a) else 'none'


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
