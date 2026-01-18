import sys
from pathlib import Path
import shutil

restructure_file = Path(sys.argv[1]).resolve()

def parse():
    lines = [
        line.rstrip()
        for line in restructure_file.read_text().splitlines()
        if line.strip()
    ]

    if not lines or not lines[0].startswith("using "):
        raise RuntimeError("First line must be: using <path>")

    root = Path(lines[0][6:]).resolve()
    if not root.exists() or not root.is_dir():
        raise RuntimeError(f"Invalid root path: {root}")

    sections = {}
    current = None

    for line in lines[1:]:
        if line.endswith(":"):
            current = line[:-1]
            sections[current] = []
        else:
            if current is None:
                raise RuntimeError("Entry outside of a section")
            sections[current].append(line.strip())

    return root, sections

def all_files(root: Path):
    return {p.resolve() for p in root.rglob("*") if p.is_file()}

def move_with_prefix(root: Path, src: Path, order: str):
    rel = src.relative_to(root)
    top, *rest = rel.parts
    dest = root / f"{order}_{top}" / Path(*rest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.move(str(src), str(dest))

def run_prefix(root: Path, rules):
    original_files = all_files(root)
    claimed = set()
    catch_all = None

    for rule in rules:
        order, target = rule.split(maxsplit=1)

        if target == ".":
            if catch_all is not None:
                raise RuntimeError("Multiple catch-all (N .) entries")
            catch_all = order
            continue

        path = root / target
        if not path.exists():
            raise RuntimeError(f"Missing path in prefix rule: {target}")

        if path.is_file():
            claimed.add(path.resolve())
            move_with_prefix(root, path, order)
        else:
            for f in path.rglob("*"):
                if f.is_file() and f.resolve() not in claimed:
                    claimed.add(f.resolve())
                    move_with_prefix(root, f, order)

    if catch_all is not None:
        for f in original_files:
            if f not in claimed:
                move_with_prefix(root, f, catch_all)

def run_rename(root: Path, rules):
    for rule in rules:
        src_rel, dst_rel = rule.split(maxsplit=1)
        src = root / src_rel
        dst = root / dst_rel

        if not src.exists():
            raise RuntimeError(f"Rename source missing: {src_rel}")
        if dst.exists():
            raise RuntimeError(f"Rename destination exists: {dst_rel}")

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

def cleanup(root: Path):
    for p in sorted(root.glob("**/*"), reverse=True):
        if p.is_dir() and not any(p.iterdir()):
            p.rmdir()

def main():
    if not restructure_file.exists():
        raise RuntimeError(".restructure file not found")

    root, sections = parse()

    if "prefix" in sections:
        run_prefix(root, sections["prefix"])

    if "rename" in sections:
        run_rename(root, sections["rename"])

    cleanup(root)

if __name__ == "__main__":
    main()
