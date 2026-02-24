from __future__ import annotations

import json
import shutil
from pathlib import Path


OUTPUT_FOLDER = "output"
REPORT_FOLDER = "report"
DISTRICT_REGISTRY_FOLDER = "district_id_registry"
DISTRICT_MIN = 1
DISTRICT_MAX = 15
FIRST_CONFIRM_TEXT = "reset"
SECOND_CONFIRM_TEXT = "YES"


def default_district_registry(district_number: int) -> dict:
    return {
        "district_number": district_number,
        "district_label": f"District {district_number}",
        "last_id_number": 0,
        "records": {},
    }


def reset_folder(folder_path: Path) -> None:
    if folder_path.exists():
        shutil.rmtree(folder_path)
        print(f"Removed: {folder_path}")
    folder_path.mkdir(parents=True, exist_ok=True)
    print(f"Created: {folder_path}")


def reset_output_folder(project_root: Path) -> None:
    reset_folder(project_root / OUTPUT_FOLDER)


def reset_report_folder(project_root: Path) -> None:
    reset_folder(project_root / REPORT_FOLDER)


def reset_district_registry(project_root: Path) -> None:
    registry_root = project_root / DISTRICT_REGISTRY_FOLDER
    reset_folder(registry_root)

    for district_number in range(DISTRICT_MIN, DISTRICT_MAX + 1):
        registry_path = registry_root / f"district_{district_number:02d}.json"
        registry_path.write_text(
            json.dumps(default_district_registry(district_number), indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
        print(f"Initialized: {registry_path}")


def confirm_reset() -> bool:
    first = input("Type 'reset' to continue: ").strip()
    if first != FIRST_CONFIRM_TEXT:
        print("Reset cancelled (first confirmation did not match).")
        return False

    second = input("Are you really sure? Type 'YES' to reset: ").strip()
    if second != SECOND_CONFIRM_TEXT:
        print("Reset cancelled (second confirmation did not match).")
        return False

    return True


def main() -> None:
    if not confirm_reset():
        return

    project_root = Path(__file__).resolve().parent
    reset_output_folder(project_root)
    reset_report_folder(project_root)
    reset_district_registry(project_root)
    print("Reset complete.")


if __name__ == "__main__":
    main()
