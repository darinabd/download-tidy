import shutil
from itertools import chain
from pathlib import Path

CATEGORIES = {
    ".pdf": "Documents",
    ".doc": "Documents",
    ".docx": "Documents",
    ".txt": "Documents",
    ".pptx": "Presentations",
    ".py": "Code",
    ".ipynb": "Code",
    ".patch": "Code",
    ".json": "Data",
    ".csv": "Data",
    ".mp3": "Audio",
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".zip": "Archives",
    ".gz": "Archives",
    ".7z": "Archives",
}


def candidate_paths(target: Path):
    yield target
    index = 1
    while True:
        yield target.with_name(f"{target.stem} ({index}){target.suffix}")
        index += 1


def destination_for(source: Path) -> Path:
    category = CATEGORIES[source.suffix.lower()]
    return source.parent / category / source.name


def build_plan(folder: Path) -> list[tuple[Path, Path]]:
    reserved = set()
    plan = []

    for source in sorted(Path(folder).iterdir()):
        if source.name.startswith(".") or source.is_symlink() or not source.is_file():
            continue
        if source.suffix.lower() not in CATEGORIES:
            continue

        target = destination_for(source)
        if target.parent.is_symlink() or (
            target.parent.exists() and not target.parent.is_dir()
        ):
            # Keep this item so apply can report the blocked destination.
            plan.append((source, target))
            continue

        for candidate in candidate_paths(target):
            reservation = (candidate.parent, candidate.name.casefold())
            if reservation in reserved or candidate.exists() or candidate.is_symlink():
                continue

            reserved.add(reservation)
            plan.append((source, candidate))
            break

    return plan


def move_file(source: Path, planned_target: Path) -> Path:
    """Reserve a free destination before moving the source."""
    directory = planned_target.parent

    if source.is_symlink() or not source.is_file():
        raise OSError("source is no longer a regular file")
    if directory.is_symlink():
        raise OSError(f"destination directory is a symbolic link: {directory.name}")

    directory.mkdir(exist_ok=True)
    candidates = candidate_paths(directory / source.name)

    for candidate in chain((planned_target,), candidates):
        try:
            with candidate.open("xb"):
                pass
        except FileExistsError:
            continue

        try:
            shutil.move(str(source), str(candidate))
        except OSError:
            candidate.unlink()
            raise

        return candidate
