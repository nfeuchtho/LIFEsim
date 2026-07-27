# Stage B on bluesky

The six two-dimensional operating-point scans at null order four, run with the
physical beam combiner. Each is a grid of endpoint searches -- 15 x 15 for the
magnitude and slew scans -- so each is hours and all six are of order a day.
They are separable, and should be submitted separately.

## Getting it there

Copy the whole `LIFESim` tree with WinSCP. The catalogues under
`lifesim/catalogs/` are gitignored and are 181 MB and 121 MB, so a clone would
not bring them; a direct copy does.

## Environment

```bash
python -m venv ~/venv-lifesim          # or use the cluster's existing venv
source ~/venv-lifesim/bin/activate
cd ~/LIFESim
pip install -r requirements.txt
pip install -e . --no-deps
```

The last line matters. Without it `import lifesim` only works when the current
directory happens to be the repository root, which is exactly the kind of thing
that fails inside a batch job.

Check it before queueing anything:

```bash
cd /tmp && python -c "import lifesim; print(lifesim.__file__)"
```

Matplotlib is already forced to the Agg backend inside the collection script, so
no display is needed. `trade_space_explorer` used to select `Qt5Agg`
unconditionally at import, which overrode that and failed on a headless node; it
now leaves an already-chosen non-interactive backend alone and never raises if Qt
is missing. Belt and braces, you can also export it:

```bash
export MPLBACKEND=Agg
```

which the module honours and will not override.

## Running

One scan per job. `--n-cpu` is the main lever: the SNR flow is dispatched across
that many workers and the default of eight comes from `settings.yaml`, not from
anything about the problem. Set it to the cores you are allocated.

```bash
python -u -m lifesim.ams.ablation_throughput --stage-b mag    --catalog hi --n-cpu 32
python -u -m lifesim.ams.ablation_throughput --stage-b mag    --catalog lo --n-cpu 32
python -u -m lifesim.ams.ablation_throughput --stage-b slew   --catalog hi --n-cpu 32
python -u -m lifesim.ams.ablation_throughput --stage-b slew   --catalog lo --n-cpu 32
python -u -m lifesim.ams.ablation_throughput --stage-b linear --catalog hi --n-cpu 32
python -u -m lifesim.ams.ablation_throughput --stage-b linear --catalog lo --n-cpu 32
```

**Use `python -u`.** The search routine prints its per-iteration progress without
flushing, and Python block-buffers stdout when it is not a terminal, so without
`-u` the log stays empty for hours and a working job is indistinguishable from a
hung one. This was verified locally: the runner's own headers appeared, the
search progress did not.

Each writes its figure to `thesis/images/tse/physical/` as soon as it finishes,
named `phys_<catalog>_<scan>_<target>.pdf`, and prints its elapsed time. Nothing
is written until a scan completes, so a job killed by a wall-clock limit leaves
nothing behind -- prefer a generous limit over a tight one.

If bluesky uses SLURM, wrap each line:

```bash
#!/bin/bash
#SBATCH --job-name=life-stageb-mag-hi
#SBATCH --cpus-per-task=32
#SBATCH --time=24:00:00
#SBATCH --output=stageb-mag-hi-%j.out
source ~/venv-lifesim/bin/activate
cd ~/LIFESim
python -u -m lifesim.ams.ablation_throughput --stage-b mag --catalog hi --n-cpu 32
```

## Bringing the results back

Only two directories matter:

- `thesis/images/tse/physical/` -- the figures
- `thesis/reproducibility/` -- any TSVs and logs

## Sanity check before committing a night to it

Run the cheap mode first. It finishes in about twenty minutes and exercises the
same architecture, combiner and baseline code the scans use:

```bash
python -m lifesim.ams.ablation_throughput --physical --catalog hi --n-cpu 32
```

If that produces twelve rows in
`thesis/reproducibility/physical_architecture.tsv` and twelve figures, the long
scans will run.

## What these figures are for

They replace the order-four operating-point figures in the thesis, which were
produced with the `sin^n` shape proxy. The order-two figures do **not** need
regenerating: the reference architecture is unchanged and the combiner framework
reproduces its results to 0.012 %.
