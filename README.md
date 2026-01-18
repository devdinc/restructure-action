# Repository Restructure Action

A GitHub Action that **deterministically restructures repository files and folders** based on a declarative `.restructure` file.

This action is designed for **large repositories**, **monorepos**, or **script-heavy projects** where folder layout and execution order must be controlled explicitly and reproducibly.

---

## Features

* Triggered on **pushes** (typically to `stable`)
* Pulls from a **Git ref** (branch / tag / commit SHA)
* Applies restructuring rules to a target folder
* Supports **files and folders**
* Preserves folder hierarchies
* Supports **all file extensions**
* Explicit failure on invalid references
* Optional catch-all behavior
* Force-pushes results back to the executing branch
* Fully deterministic and idempotent

---

## How It Works (High-Level)

1. The action checks out the current branch.
2. It fetches and resets the repository to a specified source ref.
3. It reads `.restructure`.
4. It applies restructuring rules to the specified folder.
5. It commits and **force-pushes** the changes back to the branch that triggered the action.

---

## Usage

### Example Workflow

```yaml
name: Restructure Scripts

on:
  push:
    branches:
      - stable

jobs:
  restructure:
    runs-on: ubuntu-latest
    steps:
      - uses: your-org/restructure-action@v1
        with:
          source-ref: stable
          restructure-file: .restructure
```

---

## Inputs

| Input              | Description                                    | Default        |
| ------------------ | ---------------------------------------------- | -------------- |
| `source-ref`       | Git ref to pull from (branch, tag, commit SHA) | `stable`       |
| `restructure-file` | Path to the `.restructure` file                | `.restructure` |

---

## `.restructure` File Format

### Required Header

The first line **must** define the root path:

```
using <path>
```

Examples:

```
using scripts
using src/game/scripts
using .
```

All subsequent paths are **relative to this root**.

---

## Modes

The `.restructure` file supports **multiple modes**, applied **top to bottom**.

Currently supported:

* `prefix:` — order-based prefixing
* `rename:` — explicit rename / move rules

---

## `prefix:` Mode

### Purpose

Deterministically prefixes top-level folders based on numeric order.

### Syntax

```
prefix:
  <N> <path>
  <N> .
```

### Rules

* `<path>` may be:

  * a file
  * a folder
  * `.`
* Exactly **zero or one** `N .` entry is allowed
* Folder structure is preserved
* Files not matched are **allowed to remain untouched**
* Missing paths cause failure

### Example

```
using scripts

prefix:
  0 util
  1 libs/functionsv2.sk
  2 libs/routines
  3 .
```

### Result

```
scripts/
├── 0_util/
│   └── ...
├── 1_libs/
│   └── functionsv2.sk
├── 2_libs/
│   └── routines/
│       └── ...
├── 3_<everything_else>/
```

---

## Specificity Rules

When paths overlap:

1. File rules win over folder rules
2. Deeper paths win over shallower paths
3. `.` (catch-all) applies last

---

## `rename:` Mode

### Purpose

Explicit renaming or moving of files or folders.

### Syntax

```
rename:
  <from> <to>
```

### Rules

* Paths are relative to `using <path>`
* `<from>` must exist
* `<to>` must not exist
* Parent directories are created automatically
* Applied **after `prefix:`**

### Example

```
rename:
  util 0_util
  libs/functionsv2.sk 0_libs/functionsv2.sk
```

---

## Combined Example

```
using scripts

prefix:
  0 util
  1 libs/functionsv2.sk
  2 libs/routines
  3 .

rename:
  3_libs/pdc.sk legacy/pdc.sk
```

---

## Failure Conditions

The action **fails immediately** if:

* `using <path>` is missing or invalid
* A referenced file or folder does not exist
* More than one `N .` entry exists
* A rename source does not exist
* A rename destination already exists
* The `.restructure` file is malformed

> Prefix mode **does not fail** if some files are left untouched.

---

## Git Behavior

* The repository is reset to the specified `source-ref`
* Changes are committed automatically
* The action **force-pushes** to the branch that triggered the workflow

This ensures:

* Deterministic output
* No merge conflicts
* Repeatable runs

---

## Best Practices

* Keep `.restructure` version-controlled
* Use `prefix:` for bulk ordering
* Use `rename:` for exceptions or fine-grained control
* Use `N .` only when you want full coverage

Just say which.
