#!/usr/bin/env bash
#
# Refresh the bundled nwnscriptcomp libraries from a neverwinter.nim release.
#
# The latest stable release is used by default; pass a tag to pin a specific
# one instead, e.g. ./update.sh 2.3.1

set -euo pipefail

repo="niv/neverwinter.nim"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tag="${1:-}"

if [ -z "$tag" ]; then
    echo "Resolving latest stable release of $repo..."
    tag="$(
        curl -fsSL "https://api.github.com/repos/$repo/releases/latest" |
            python3 -c 'import json, sys; print(json.load(sys.stdin)["tag_name"])'
    )"
fi

echo "Using neverwinter.nim release $tag"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# <platform directory>:<release target>:<library extension>
platforms=(
    "linux_x86_64:x86_64-linux-gnu:so"
    "linux_aarch64:aarch64-linux-gnu:so"
    "macos_x86_64:x86_64-macos:dylib"
    "macos_aarch64:aarch64-macos:dylib"
    "windows_x86_64:x86_64-windows:dll"
    "windows_aarch64:aarch64-windows:dll"
)

for platform in "${platforms[@]}"; do
    IFS=: read -r dir target ext <<<"$platform"
    archive="neverwinter-$target.zip"
    url="https://github.com/$repo/releases/download/$tag/$archive"

    echo "Fetching $archive -> $dir/libnwnscriptcomp.$ext"
    curl -fsSL "$url" -o "$tmp/$archive"
    mkdir -p "$here/$dir"
    unzip -o -j "$tmp/$archive" "*libnwnscriptcomp.$ext" -d "$here/$dir" >/dev/null
done

cat >"$here/README.txt" <<EOF
Script compiler binaries imported from neverwinter.nim release $tag:

https://github.com/$repo/releases/tag/$tag
EOF

echo "Done."
