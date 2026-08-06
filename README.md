# Immunoinformatics-plugin

The Horus plugin for BSC - Immunoinformatics

## TCoaRse

The `TCoaRse` block category predicts TCR-pMHC binding from a folder of
AlphaFold3 models. It is a Horus port of
[TCoaRse-nf](https://github.com/BSC-CNS-EAPM/TCoaRse-nf)'s
`tcoarse_prediction.nf`: one block per Nextflow process, same scripts, same
outputs, plus the **TCoaRse** flow preset with the whole pipeline wired.

The 15 blocks, the configuration and the flow are documented in
**[docs/TCoaRse.md](docs/TCoaRse.md)**.

Quick start:

1. *Settings > Plugins > Immunoinformatics > TCoaRse*: set the TCoaRse-nf
   installation folder and the python executable of an environment that has its
   dependencies (torch, transformers, DockQ, tcrdist, anarci...). The plugin
   does not install them.
2. Open the **TCoaRse** flow preset, select the AlphaFold3 outputs folder in the
   *AF3 Outputs* block and run.

### Tests

```bash
python Tests/test_tcoarse_blocks.py          # or: python -m pytest Tests -vv
```

The tests fake the block runtime and replace the job launcher with a recorder,
so they check the command, the uploaded files and the outputs of every block
without needing the TCoaRse dependencies or a cluster. Point `HORUS_PATH` at the
Horus checkout if it is not in `~/GitHub/horus`.

Regenerate the flow preset after changing any block id:

```bash
python Devtools/generate_tcoarse_flow.py
```
