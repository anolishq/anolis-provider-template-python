# AGENTS.md: anolis-provider-template-python

The template every Python provider starts from. Changes here reach every
provider made from it afterwards, so keep it small: one synthetic device, the
SDK, and the build and release a provider needs.

## Build / test

- `just setup`, then `just check` (format, lint, strict typecheck) and `just test` (unit tests and the conformance
  harness). CI also builds the frozen binary on x86_64 and arm64 and runs the harness against it.
- The required CI status check is the **`ok`** job; never merge red.
- `tests/test_conformance.py` requires the harness to pass with no skips beyond `EXPECTED_SKIPS`, which is empty.

## Rules

- **Self-contained.** CI and release use only public actions and public anolishq releases: no reusable anolishq
  workflows, actions or secrets. A provider made from the template must build and release in any account.
- **`scripts/rename.sh` must keep working.** The `rename` CI job renames the template and runs the checks; a new
  file or path that names the template has to be covered by the script.
- **The heater stays a teaching example.** It shows the patterns a real provider needs (a safe state for ACTUATE, an
  argument-free function with a result, `stop`, `check_config`) and nothing a real provider would not.
- The SDK is pinned by commit in `pyproject.toml` until it is published.
- The template is never tagged or released itself.
- An outside instance generated from this template proves the path from another account; if the build or release
  path changes, repeat that proof (see the README).
