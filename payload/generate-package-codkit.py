#!/usr/bin/env python3
"""Render the `vibe.toml` of the `org.vibevm.codkit` package family.

    vibevm-generate-package-codkit --codkit 1.0.0 SHA256SUMS SIZES > vibe.toml

The family holds one package today, `org.vibevm.codkit/codkit`, and this is
the only renderer of its manifest: the package repository carries the
rendered `vibe.toml` and no tooling of its own. A second family member
becomes a second flag here, beside `--codkit`.

`SHA256SUMS` is the checksum asset of the pinned Codkit GitHub release and
`SIZES` a file of `<bytes> <name>` lines for the same archives (for example
`stat -c '%s %n' *`). Nothing is fetched and nothing is written: download the
archives, verify each against `SHA256SUMS`, then render on standard output.

Rendering is deterministic. The same release version and the same two input
files produce byte-identical output, whatever directory they are read from —
the header records each input by base name and SHA-256, never by path, and
carries no clock. Re-render before every publish and compare.
"""
import argparse
import hashlib
import os
import sys

GENERATOR = "org.vibevm.codkit/vibevm-package-generator"
GENERATOR_VERSION = "1.0.0"
COMMAND = "vibevm-generate-package-codkit"

CODKIT_RELEASES = "https://github.com/vibevm/codkit/releases/download"

# option id, platform, platform name, arch, arch name, codkit asset suffix
TARGETS = [
    ("linux-x64", "linux", "Linux (glibc)", "x86_64", "Intel/AMD 64-bit", "linux-x64.tar.gz"),
    ("linux-arm64", "linux", "Linux (glibc)", "aarch64", "ARM 64-bit", "linux-arm64.tar.gz"),
    ("linux-musl-x64", "linux-musl", "Linux (musl: Alpine and others)", "x86_64", "Intel/AMD 64-bit", "linux-x64-musl.tar.gz"),
    ("macos-x64", "macos", "macOS", "x86_64", "Intel 64-bit", "darwin-x64.tar.gz"),
    ("macos-arm64", "macos", "macOS", "aarch64", "Apple silicon", "darwin-arm64.tar.gz"),
    ("windows-x64", "windows", "Windows", "x86_64", "Intel/AMD 64-bit", "win32-x64.zip"),
    ("windows-arm64", "windows", "Windows", "aarch64", "ARM 64-bit", "win32-arm64.zip"),
]


def sums(path):
    table = {}
    with open(path, encoding="utf-8") as text:
        for line in text:
            parts = line.split()
            if len(parts) == 2:
                table[parts[1].lstrip("*")] = parts[0]
    return table


def sizes(path):
    table = {}
    with open(path, encoding="utf-8") as text:
        for line in text:
            parts = line.split()
            if len(parts) == 2:
                table[parts[1].rsplit("/", 1)[-1]] = int(parts[0])
    return table


def digest(path):
    """The SHA-256 of one input file, so the manifest records what it was
    rendered from and a stale input is visible in a diff."""
    sha = hashlib.sha256()
    with open(path, "rb") as blob:
        for chunk in iter(lambda: blob.read(1 << 20), b""):
            sha.update(chunk)
    return sha.hexdigest()


def provenance(codkit, inputs):
    """The header comment: who rendered the file, from what, and the exact
    command that renders it again. Base names only and no timestamp, so the
    header is part of what re-rendering reproduces byte for byte."""
    lines = [
        f"# Rendered by {GENERATOR} {GENERATOR_VERSION} ({COMMAND}). Do not edit.",
    ]
    for path in inputs:
        name = os.path.basename(path)
        lines.append(f"# input {name} sha256 = {digest(path)}")
    names = " ".join(os.path.basename(path) for path in inputs)
    lines.append(f"# re-render: {COMMAND} --codkit {codkit} {names} > vibe.toml")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        prog=COMMAND,
        description="Render the vibe.toml of an org.vibevm.codkit package.",
    )
    parser.add_argument(
        "--codkit",
        required=True,
        metavar="VERSION",
        help="the Codkit release to render, for example 1.0.0",
    )
    parser.add_argument("sums", metavar="SHA256SUMS", help="the release's checksum asset")
    parser.add_argument("sizes", metavar="SIZES", help="`<bytes> <name>` lines for the archives")
    args = parser.parse_args()

    codkit = args.codkit
    codkit_sums, size = sums(args.sums), sizes(args.sizes)
    out = [provenance(codkit, [args.sums, args.sizes]) + HEADER.format(codkit=codkit)]
    for option, platform, platform_name, arch, arch_name, suffix in TARGETS:
        archive = f"codkit-{codkit}-{suffix}"
        root = archive.rsplit(".tar.gz", 1)[0].rsplit(".zip", 1)[0]
        if archive not in codkit_sums:
            parser.error(f"`{args.sums}` has no digest for `{archive}`")
        if archive not in size:
            parser.error(f"`{args.sizes}` has no size for `{archive}`")
        out.append(OPTION.format(
            option=option, platform=platform, platform_name=platform_name,
            arch=arch, arch_name=arch_name, codkit=codkit,
            fmt="zip" if suffix.endswith(".zip") else "tar_gz",
            url=f"{CODKIT_RELEASES}/v{codkit}/{archive}", sha=codkit_sums[archive],
            size=size[archive], payload_root=root,
        ))
    sys.stdout.write("\n".join(out))


HEADER = '''[package]
name = "codkit"
group = "org.vibevm.codkit"
kind = "app"
version = "{codkit}"
epoch = 1
format = "normal"
authors = ["Oleg Chirukhin"]
license = "UPL-1.0"
description = "Codkit {codkit}, the patch-set manager for fork trees, as a portable Vibe application running on the Node.js of the machine"
keywords = ["codkit", "patch-set", "fork", "upstream", "application"]
homepage = "https://github.com/vibevm/codkit"

[compatibility]
min_vibe_version = "1.0.12"
requires_kinds = []

[application]
id = "codkit"
keywords = ["codkit", "patches", "fork"]
'''

# One archive and one launcher per target. The launcher names the command
# `node` instead of a file in the payload, so Codkit runs on whichever
# Node.js 22.6+ is on PATH when it starts: the machine's own, or the one
# `vibe install -g org.vibevm.node/node` puts there. The package bundles no
# runtime and requires no other package.
OPTION = '''
[[installer_options]]
id = "{option}"
name = "Codkit {codkit}"
platform = "{platform}"
platform_name = "{platform_name}"
arch = "{arch}"
arch_name = "{arch_name}"

[[installer_options.steps]]
id = "codkit"
title = "Download and unpack the Codkit {codkit} offline bundle"
kind = "archive"
format = "{fmt}"
source = "{url}"
sha256 = "{sha}"
size = {size}
payload_root = "{payload_root}"

[[installer_options.launchers]]
id = "codkit"
name = "codkit"
description = "Codkit command line (runs on the `node` found on PATH)"
executable = "command:node"
args = ["$app_root/node_modules/codkit/bin/codkit.mjs"]
kind = "command"
default = true

[[installer_options.public_commands]]
name = "codkit"
launcher = "codkit"
'''

if __name__ == "__main__":
    main()
