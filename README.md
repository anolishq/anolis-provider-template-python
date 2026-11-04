# anolis-provider-template-python

A template for an [Anolis](https://github.com/anolishq/anolis) device provider
in Python, built on the
[Python provider SDK](https://github.com/anolishq/anolis-provider-sdk-python).
It runs as is: each configured device is a simulated heater, so it needs no
hardware. Replace the heater with your device and keep the rest.

What it gives you, all passing in CI:

- A provider that passes the
  [anolis-protocol](https://github.com/anolishq/anolis-protocol) conformance
  harness at level 2 with no skips.
- A frozen single-file binary for linux x86_64 and arm64, also run under the
  harness.
- A release workflow that publishes what
  [`install.sh`](https://github.com/anolishq/anolis/blob/main/docs/deploy/install-sh.md#what-a-provider-release-must-provide)
  and the Workbench read, so a machine profile can pin your repository from any
  GitHub account.

CI and release depend on nothing of anolishq's beyond public releases, so the
same workflows run in your account.

## Start a provider from it

1. Click **Use this template** and create your repository.
2. Rename it to your provider's kind, which must use `a-z`, `0-9` and `-` and
   start with a letter:

   ```sh
   scripts/rename.sh bme280-lab   # binary: anolis-provider-bme280-lab
   ```

3. Change `.github/CODEOWNERS` to your account, and this README to describe
   your provider.
4. Replace the heater in `src/<package>/provider.py` with your device: declare
   its signals and functions, its config, and `read`, `call` and `stop`. The
   [provider guide](https://github.com/anolishq/anolis-provider-sdk-python/blob/main/docs/writing-a-provider.md)
   covers each, and its "Vendor drivers" section covers wrapping a vendor's
   driver library.
5. Keep `config/conformance.yaml` runnable without hardware (a mock mode), so
   the harness and CI can drive your provider anywhere.
6. Check and test:

   ```sh
   just setup
   just check
   just test
   ```

7. Release: set `version` in `pyproject.toml`, then push a matching tag
   (`v0.1.0`).

## The device

`heater` has a first-order thermal model. Its temperature approaches
`ambient_c` plus `max_rise_c` times the power level, with a 60 s time
constant, and it counts the energy it draws at `rated_w`.

| Signal | Type | |
| --- | --- | --- |
| `temperature` | double, degC | |
| `power` | double, 0 to 1 | |
| `energy` | double, J | not in the default set |

| Function | Category | |
| --- | --- | --- |
| `set_power(power: 0..1)` | ACTUATE | 0 is the safe state, so the runtime can stop it |
| `reset_energy()` | CONFIG | returns the energy count it cleared |

The provider turns every heater off when it exits, however the session ends.

## Install

This template is never released itself; a provider made from it is, under its
own name. Pin that release in a machine profile, from whichever account holds
it:

```yaml
components:
  providers:
    bme280-lab:
      repo: <your-account>/anolis-provider-bme280-lab
      version: "0.1.0"
```

## Licence

Apache-2.0.
