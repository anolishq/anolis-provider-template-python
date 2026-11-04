# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A provider of simulated heaters on the Python provider SDK, passing the
  conformance harness at level 2 with no skips, from source and as a frozen
  binary on x86_64 and arm64.
- A release workflow publishing what `install.sh` and the Workbench read, plus
  the tagged source for the ADPP compatibility matrix.
- `scripts/rename.sh`, which renames the provider after "Use this template".
