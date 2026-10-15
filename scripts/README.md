# Scripts

Helper scripts for developing CardDemo against a remote z/OS host. Most of them submit JCL to JES over FTP through a local tunnel.

## Prerequisites

- An FTP tunnel to the mainframe listening on `localhost:2121`. Each remote script checks `ps f` for `2121:` and exits with `FTP Tunnel to Ensono not running.` if it isn't there.
- `tnftp` on the PATH.
- Paths are relative to the working directory, and each script expects a different one. `run_*.sh` and `remote_refresh.sh` reference `jcl/<member>.jcl`, so run them from `app/`. `upld_module.sh` references `scripts/pad.awk`, so run it from the repo root. `remote_compile.sh` reads `./compile_batch.jcl.template`, so run it from `scripts/`.
- Datasets under the HLQ `AWS.M2.CARDDEMO` (`.CBL`, `.CPY`, `.LISTING`, `.LOADLIB`, ...). Change the HLQ in the scripts and template if yours is different.

## Build and upload

| Script | Usage | What it does |
|---|---|---|
| `upld_module.sh` | `upld_module.sh <path> <type>` | Pads the file to 80-byte records with `pad.awk` (this rewrites the file in place), then uploads it to `'AWS.M2.CARDDEMO.<type>(<member>)'` |
| `remote_compile.sh` | `remote_compile.sh <file> <ext> <member>` | `.cbl` only. Runs `make -f Makefile` (not included in this repo), replaces `ZZZZZZZZ` in `compile_batch.jcl.template` with the member name, and submits the job |
| `compile_batch.jcl.template` | used by `remote_compile.sh` | Batch compile + link: `IGYCRCTL` (Enterprise COBOL `IGY.SIGYCOMP.V63`), then `IEBGENER` copies the listing to SYSOUT, then `HEWL` link-edits into `AWS.M2.CARDDEMO.LOADLIB` |
| `local_compile.sh` | `local_compile.sh` | One-line GnuCOBOL syntax check (`cobc --std=ibm-strict -I ../cpy/`). The path to `sample/cobol/SIZING.cbl` is hard-coded, so edit it before use |
| `pad.awk` | `awk -f pad.awk <file>` | Pads every line to exactly 80 characters and replaces CR with a space |

## Submit and run batch

These scripts submit their jobs in a fixed order with `sleep` between steps. They don't check return codes, so check JES output after each run.

| Script | Job sequence |
|---|---|
| `remote_submit.sh <file> <ext>` | Submits a single `.jcl` file |
| `remote_refresh.sh` | `CLOSEFIL` → reload ACCT, CARD, XREF, CUST, TRAN, DISCGRP, TCATBALF, TRANCATG, TRANTYPE, DUSRSECJ → `OPENFIL` |
| `run_posting.sh` | `CLOSEFIL` → `ACCTFILE` → `TCATBALF` → `TRANBKP` → `POSTTRAN` → `TRANIDX` → `OPENFIL` |
| `run_interest_calc.sh` | `CLOSEFIL` → `INTCALC` → `TRANBKP` → `COMBTRAN` → `TRANIDX` → `OPENFIL` |
| `run_full_batch.sh` | Full data refresh, then `POSTTRAN` → `INTCALC` → `TRANBKP` → `COMBTRAN` → `TRANIDX` → `OPENFIL` |

`CLOSEFIL` and `OPENFIL` close and reopen the VSAM files in CICS, so the online region can't use those files while a script is running.

## Source versioning

| Script | Usage | What it does |
|---|---|---|
| `git-addSrcVersionInfo.sh` | `git-addSrcVersionInfo.sh <file>` | Adds or updates a `Ver: CardDemo_<tag>-<commits> Date: ...` comment in a `.cbl/.cob/.cpy`, `.jcl/.prc/.proc`, `.bms` or `.py` source file, using the right comment syntax for each. **Side effect:** it deletes every local git tag except `app_version` (set to `v2.0` at the top of the script) |

## `markers/`

Empty files named after members (`CBACT04C`, `POSTTRAN`, `CVACT01Y`, ...). They look like timestamp targets for the `make`-based upload flow that `remote_compile.sh` calls. That Makefile is not in the repo.
