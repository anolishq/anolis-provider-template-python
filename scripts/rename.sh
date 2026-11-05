#!/usr/bin/env bash
# Rename this provider after "Use this template".
#
#   scripts/rename.sh <kind>
#
# <kind> names the provider: the binary becomes anolis-provider-<kind>, which is
# also what install.sh and machine profiles call it. It uses a-z, 0-9 and -,
# starting with a letter. Every tracked file and path that names the provider is
# rewritten, then the lock file is refreshed if uv is installed. Review the
# result with `git diff --stat` and commit it.
set -euo pipefail

kind="${1:-}"
if ! [[ "$kind" =~ ^[a-z][a-z0-9-]*$ ]] || [[ "$kind" == *- ]]; then
  echo "usage: $0 <kind>   (a-z, 0-9 and -, starting with a letter, e.g. bme280-lab)" >&2
  exit 2
fi
cd "$(git rev-parse --show-toplevel)"

# The current name comes from pyproject.toml, not from this script, so the
# script renames from whatever the provider is called now: the template's name
# the first time, the provider's own name after that.
old_dash="$(sed -n 's/^name = "\(anolis-provider-[a-z0-9-]*\)"$/\1/p' pyproject.toml | head -n 1)"
if [ -z "$old_dash" ]; then
  echo "pyproject.toml has no project name of the form anolis-provider-<kind>" >&2
  exit 2
fi
old_snake="${old_dash//-/_}"
new_dash="anolis-provider-${kind}"
new_snake="anolis_provider_${kind//-/_}"
self="scripts/rename.sh"

if [ "$new_dash" = "$old_dash" ]; then
  echo "already named $old_dash" >&2
  exit 2
fi

# File contents.
git ls-files -z | while IFS= read -r -d '' f; do
  [ "$f" = "$self" ] && continue
  if grep -qF -e "$old_dash" -e "$old_snake" -- "$f"; then
    sed -i -e "s/${old_dash}/${new_dash}/g" -e "s/${old_snake}/${new_snake}/g" -- "$f"
  fi
done

# Paths: the package directory and the PyInstaller spec.
git mv "src/${old_snake}" "src/${new_snake}"
git mv "packaging/${old_dash}.spec" "packaging/${new_dash}.spec"

if command -v uv >/dev/null 2>&1; then
  uv lock
fi

echo "Renamed to ${new_dash}. Next:"
echo "  - change .github/CODEOWNERS to your account, and the README's title and text"
echo "  - replace the heater in src/${new_snake}/provider.py with your device"
echo "  - just setup && just check && just test"
