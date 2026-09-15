# build-xpi

GitHub Action to build `.xpi` packages for UXP-based applications (Pale Moon, Ambassador, Epyrus, and applications using the Firefox or Thunderbird GUID). It pulls metadata out of `install.rdf`, tags the filename with the target app codes, handles dev vs release versioning, and zips everything up cleanly.

## What it does

1. **Builds the filename from your manifest:** Reads the version and target applications directly from `install.rdf`.

- Maps application GUIDs to short codes:
  - Pale Moon: `pm`
  - Firefox: `fx`
  - Thunderbird: `tb`
  - Ambassador: `am`
  - Epyrus: `es`
- Example output: `sample-package-1.0.0-pm+tb+am+es.xpi`

2. **Handles dev builds automatically:**

- If triggered by a Git tag: uses the version in `install.rdf` as-is.
- If triggered by a branch push or PR: appends the short commit hash (`1.0.0.a1b2c3d`) to both the file name and the `install.rdf` inside the package.

3. **Uploads build artifact:** The `.xpi` is automatically uploaded as a workflow artifact.

4. **Root or `src/` builds:** Works whether your addon files live in a `src/` folder or right at the root of the repo.

## Inputs

| Name           | Required | Default | Description                                                        |
| -------------- | -------- | ------- | ------------------------------------------------------------------ |
| `package-name` | yes      |         | Base name of the output file (e.g. `sample-package`).                   |
| `source-dir`   | no       | `src`   | Directory where `install.rdf` lives. Use `.` if it is at the root. |

## Outputs

| Name           | Description                                 |
| -------------- | ------------------------------------------- |
| `xpi-filename` | The exact filename of the generated `.xpi`. |

## How to set this up

Reference this action from your GitHub Actions workflow. See the sample `package.yml` below:

```yml
name: Build and Release XPI Package

on:
  push:
    branches: [main, master]
    tags: ["v*", "*.*.*"]
  pull_request:
    branches: [main, master]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Build XPI
        id: builder
        uses: FranklinDM/build-xpi@main # or @v1
        with:
          package-name: "sample-package"
          # source-dir: "." # Uncomment if files are at root, defaults to "src"

      # Optional: use if you want to automate release creation and publication too.
      - name: Create Release
        if: github.ref_type == 'tag'
        uses: softprops/action-gh-release@v3
        with:
          files: ${{ steps.builder.outputs.xpi-filename }}
          name: ${{ github.ref_name }}
          generate_release_notes: true
          prerelease: ${{ steps.builder.outputs.is-prerelease }}
```
