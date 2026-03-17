# Python Environment Strategy

This repository uses a single virtual environment at the repository root: `.venv/`.

## Why
- Keep ABM (`core/abm`), data tooling (`data`), and tests on one dependency set.
- Avoid dependency drift across subproject environments.
- Simplify onboarding and CI commands.

## Standard Setup (Linux)
From repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Build Rust Python Extensions Into The Same Env
From repository root, with `.venv` active:

```bash
cd core/lob-engine && maturin develop && cd -
cd core/friction && maturin develop && cd -
```

## Verify
From repository root, with `.venv` active:

```bash
python -c "import mesa; print('mesa ok')"
python -c "import finance_data; print('finance_data ok')"
python -c "import lob_engine; print('lob_engine ok')"
python -c "import friction_engine; print('friction_engine ok')"
```

## Migration From Nested Environments
If you created a subproject virtual environment (for example `core/abm/.venv`), stop using it and activate only the root `.venv`.

Optional cleanup:

```bash
rm -rf core/abm/.venv
```

## Team Convention
- Always run Python tooling from repository root with root `.venv` activated.
- Do not create additional `.venv` folders in subdirectories unless explicitly required for isolated experiments.
