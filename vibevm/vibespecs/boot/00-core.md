# Package generator for `org.vibevm.codkit` — application package

This package declares how Vibe installs one command,
`vibevm-generate-package-codkit`, which renders the `vibe.toml` of a package
of the `org.vibevm.codkit` family on standard output. The family holds one
package today, `org.vibevm.codkit/codkit`; this is the only renderer of its
manifest, and that package repository carries the rendered file and no
tooling.

Six installer options — Linux x86_64/aarch64, macOS x86_64/aarch64, Windows
x86_64/aarch64 — because `platform` and `arch` are both required and matched
exactly against the host (`PROP-059#installer-options`), so a command that
runs everywhere still needs one row per detectable pair. There is no
`linux-musl` row: nothing is downloaded, so a musl host is served by the
`linux` rows it is detected as. (The *rendered* manifest has seven options,
one of them musl, because that package does download archives — do not
confuse the two tables.)

One step per option: a `copy` of `payload/generate-package-codkit.py` into the
application root. An option with neither `installation` nor `[[steps]]` is
refused, and a copy of a file this repository already carries is the smallest
honest step. **Never add a download step here** — the renderer fetches nothing
and a generator that fetches is not a generator.

One launcher, one public command, both named
`vibevm-generate-package-codkit`, and `[application] id` is that same name.
The id is the slot: the three `vibevm-package-generator` packages of the three
groups share a package name, so they must not share a slot — one slot has one
default provider, and the other two generators' commands would stop
resolving. Keep the slot equal to the command.

`executable` names the interpreter as a command resolved on PATH when the
command runs, never a file in the payload: `command:python3` on Linux and
macOS, `command:py` with `args = ["-3", …]` on Windows. No Python is bundled
or downloaded. `py` rather than `python` on Windows is deliberate:
`%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe` is a Microsoft Store alias
stub that opens a Store page instead of reporting that Python is missing,
while `py` is simply absent when Python is.

Before changing the package, read `vibe.toml`, `README.md` and the renderer
itself. Two properties are load-bearing and have to survive every change:

- **The version to render is an argument** (`--codkit 1.0.0`), never a
  constant. Moving the package to a new Codkit release must change nothing in
  this repository.
- **Rendering is deterministic.** The same release version and the same two
  input files produce byte-identical output, whatever directory they are read
  from. The provenance header therefore records each input by base name and
  SHA-256 and carries no timestamp. Re-render and `diff` before every
  publish.

A second member of the `org.vibevm.codkit` family becomes a second flag beside
`--codkit` in the one renderer — not a second generator package.
