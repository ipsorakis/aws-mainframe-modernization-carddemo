# Samples

Build JCL, compile procedures and prebuilt runtime packages for CardDemo. Step 6 of the root [README](../README.md#installation) points here for compilation.

## `proc/`: compile procedures

| Proc | Compiles |
|---|---|
| `BUILDBAT.prc` | Batch COBOL programs |
| `BUILDONL.prc` | CICS COBOL programs (CICS translator, compile, link) |
| `BLDCIDB2.prc` | CICS + DB2 programs (DB2 precompile/DBRM, CICS translator, compile, link) |
| `BUILDBMS.prc` | BMS maps: physical map in the load library, symbolic map in the copybook library |

Copy them into a PROCLIB and set the symbolic dataset parameters (`&HLQ`, `&COBLIB`, `&CPYBKS`, `&LOADLIB`, `&LISTING`, ...) for your site.

## `jcl/`: sample jobs

| Job | Purpose | How to use |
|---|---|---|
| `BATCMP.jcl` | Compile a batch program with `BUILDBAT` | Replace `BATCHPGM` with the program name everywhere |
| `CICCMP.jcl` | Compile a CICS program with `BUILDONL` | Replace `CICSPGMN`; set `HLQ` |
| `CICDBCMP.jcl` | Compile a CICS + DB2 program with `BLDCIDB2` | Replace `CICSDB2P`; set `HLQ` and the DB2 `SSID` |
| `BMSCMP.jcl` | Assemble a BMS map with `BUILDBMS` | Replace `CICSMAP`; set `HLQ` |
| `IMSMQCMP.jcl` | Compile a CICS + IMS DL/I + MQ program inline (`DFHECP1$` → `IGYCRCTL` → `IEWL`), used for the authorization extension in `app/app-authorization-ims-db2-mq/` | Check the dataset names with your administrator |
| `LISTCAT.jcl` | `IDCAMS LISTCAT` of the CardDemo catalog into `AWS.M2.CARDDEMO.LISTCAT` | |
| `REPRTEST.jcl` | Run the `REPROC` proc (`app/proc/REPROC.prc`) against the transaction VSAM/backup datasets | |
| `SORTTEST.jcl` | `SORT` of the transaction backup GDG | |
| `RACFCMDS.jcl` | Sample RACF commands through `IKJEFT01` (e.g. `RALT GCICSTRN CARD ADDMEM(CT02)`) | Needs RACF admin authority |

## `m2/`: modernized runtime packages

Prebuilt CardDemo packages for rehosting on non-mainframe runtimes.

| Package | Runtime | Contents |
|---|---|---|
| `mf/CardDemo_runtime.zip` | AWS Mainframe Modernization, Micro Focus engine | `app_config.json` (S3 source, TN3270 listener on port 7000), `import_dataset.json`, `loadlib/` (compiled `.so` programs and `.MOD` maps), `catalog/` (ctl, data, jcl, proc), `csd/CARDDEMO.CSD`, `rdef/`, and `xa/` (PostgreSQL XA switch modules) |
| `unikix/UniKix_CardDemo_runtime_v1.zip` | NTT DATA UniKix (TPE online / BPE batch) | `bin/` (`carddemo.env`, `create_project`, `compile`, `compbms`, `deploy_app`, ...) and `migrated_app/` (cbl, cpy, bms, cpy-bms, jcl, proc, ctl, catlg, data) |

For UniKix: edit the paths in `bin/carddemo.env` (`BASE_DIR`, `UNIKIX`, `INSTEBM`, `VCOBOL`, license dir), source it, then run `create_project`, `compile.all` / `compbms.all`, and `deploy_app`. Note that `deploy_app` hard-codes `MIGAPP_DIR=/home/ec2-user/migrated_app`.

The UniKix zip also contains macOS `__MACOSX/` and `.DS_Store` metadata, which you can ignore.
