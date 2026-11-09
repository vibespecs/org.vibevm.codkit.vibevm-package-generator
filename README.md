# Package generator for `org.vibevm.codkit`

This package installs one command, `vibevm-generate-package-codkit`, which
renders the `vibe.toml` of a package of the `org.vibevm.codkit` family on
standard output. The family holds one package today —
[`org.vibevm.codkit/codkit`](https://github.com/vibespecs/org.vibevm.codkit.codkit)
— and this is the only renderer of its manifest: a package repository carries
its rendered manifest and no tooling of its own.

```text
vibe install -g org.vibevm.codkit/vibevm-package-generator
vibevm-generate-package-codkit --codkit 1.0.0 SHA256SUMS SIZES > vibe.toml
```

## What it reads

| Input | What it is |
| --- | --- |
| `--codkit <version>` | the Codkit release to render, for example `1.0.0` |
| `SHA256SUMS` | the checksum asset of that Codkit GitHub release |
| `SIZES` | `<bytes> <name>` lines for the same archives — `stat -c '%s %n' *` in the directory you downloaded them to |

The version is an argument, never a constant in the renderer: moving the
package to a new Codkit release changes nothing here.

The renderer fetches nothing and writes nothing. The whole workflow is
yours: download every archive of the release, verify each against
`SHA256SUMS`, measure the sizes, then render.

```text
mkdir codkit-1.0.0 && cd codkit-1.0.0
base=https://github.com/vibevm/codkit/releases/download/v1.0.0
curl -LO $base/SHA256SUMS
for a in linux-x64.tar.gz linux-arm64.tar.gz linux-x64-musl.tar.gz \
         darwin-x64.tar.gz darwin-arm64.tar.gz win32-x64.zip win32-arm64.zip; do
  curl -LO "$base/codkit-1.0.0-$a"
done
grep -F -f <(ls codkit-1.0.0-*) SHA256SUMS | sha256sum -c -
ls codkit-1.0.0-* | sort | while read f; do echo "$(stat -c '%s' "$f") $f"; done > SIZES
vibevm-generate-package-codkit --codkit 1.0.0 SHA256SUMS SIZES > vibe.toml
```

## What it writes

Seven installer options — Linux glibc x86_64/aarch64, Linux musl x86_64,
macOS x86_64/aarch64, Windows x86_64/aarch64 — each one offline bundle pinned
by URL and SHA-256, and one launcher declared `executable = "command:node"`,
so Codkit runs on whichever Node.js is on PATH when it starts and the package
bundles no runtime. Why it is shaped that way is the package's own
documentation, not this renderer's.

Above the manifest it writes a provenance header:

```toml
# Rendered by org.vibevm.codkit/vibevm-package-generator 1.0.0 (vibevm-generate-package-codkit). Do not edit.
# input SHA256SUMS sha256 = 0d4045aa…
# input SIZES sha256 = 51dedfaa…
# re-render: vibevm-generate-package-codkit --codkit 1.0.0 SHA256SUMS SIZES > vibe.toml
```

so a reader of a published manifest can tell which generator version produced
it and exactly what it was produced from, and a stale input shows up in a
diff.

## Determinism

**Re-rendering from the same inputs is byte-identical.** The header records
each input by base name and SHA-256, never by path, and carries no clock, so
the directory you render in and the moment you render do not reach the output.
Check it before every publish:

```text
vibevm-generate-package-codkit --codkit 1.0.0 SHA256SUMS SIZES | diff - vibe.toml
```

Keep `SIZES` itself deterministic — one sorted `<bytes> <name>` line per
archive, base names only — and that check passes on any machine.

## How the command runs

The package ships the renderer, not a Python: its single installer step
copies `generate-package-codkit.py` into the application root, and the
launcher names the interpreter as a command resolved on PATH when it runs —
`python3` on Linux and macOS, the PEP 397 launcher `py -3` on Windows. There
is no Microsoft Store alias stub in that choice: `py` is absent when Python is
absent, so the command refuses by name instead of opening a Store page.

| Target | Launcher runs |
| --- | --- |
| Linux, macOS | `python3 $app_root/generate-package-codkit.py` |
| Windows | `py -3 $app_root\generate-package-codkit.py` |

Nothing is downloaded at install time and nothing is bundled. The renderer is
one file of the standard library only.

## Adding a family member

A second `org.vibevm.codkit` package becomes a second flag beside `--codkit`
in the one renderer, so the whole family is rendered by one command, from one
place, at one version.

## License

UPL-1.0, see `LICENSE.md`.
