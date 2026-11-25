import argparse
import sys
from pathlib import Path

from organizer import build_plan, move_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preview or organize a Downloads folder."
    )
    parser.add_argument("folder", type=Path)
    parser.add_argument("--apply", action="store_true", help="Move the listed files")
    args = parser.parse_args()

    try:
        plan = build_plan(args.folder)
    except OSError as error:
        parser.exit(2, f"Cannot scan {args.folder}: {error}\n")

    if not args.apply:
        for source, target in plan:
            print(f"{source.name} → {target.relative_to(args.folder)}")
        print(f"Files to move: {len(plan)}")
        return 0

    errors = 0
    for source, target in plan:
        try:
            moved = move_file(source, target)
        except OSError as error:
            errors += 1
            print(f"Error moving {source.name}: {error}", file=sys.stderr)
        else:
            print(f"{source.name} → {moved.relative_to(args.folder)}")

    print(f"Moved: {len(plan) - errors} | Errors: {errors}")
    return int(errors > 0)


if __name__ == "__main__":
    raise SystemExit(main())
