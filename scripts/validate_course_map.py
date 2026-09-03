#!/usr/bin/env python3
"""Validate the declarative course-map invariants."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import yaml

COURSE_MAP_PATH = Path("course/course-map.yml")
LABS_ROOT = Path("course/labs")


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{label} must use string keys")
    return value


def _integer(mapping: Mapping[str, object], key: str, label: str) -> int:
    value = mapping.get(key)
    if type(value) is not int:
        raise ValueError(f"{label}.{key} must be an integer")
    return value


def _string_list(mapping: Mapping[str, object], key: str, label: str) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{label}.{key} must be a non-empty list of strings")
    return value


def load_course_map(path: Path = COURSE_MAP_PATH) -> Mapping[str, object]:
    try:
        return _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), "course map")
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML: {exc}") from exc


def validate_course_map(
    course_map: Mapping[str, object], labs_root: Path = LABS_ROOT
) -> tuple[int, int, int]:
    modules_value = course_map.get("modules")
    if not isinstance(modules_value, list) or not modules_value:
        raise ValueError("modules must be a non-empty list")

    modules = [_mapping(module, f"modules[{index}]") for index, module in enumerate(modules_value)]
    declared_hours = _integer(course_map, "duration_hours", "course map")
    module_hours = sum(
        _integer(module, "hours", f"modules[{index}]") for index, module in enumerate(modules)
    )

    completion = _mapping(course_map.get("course_completion"), "course_completion")
    required_hours = _integer(completion, "required_hours", "course_completion")
    if module_hours != declared_hours or required_hours != declared_hours:
        raise ValueError(
            "course hours disagree "
            f"(modules={module_hours}, duration={declared_hours}, required={required_hours})"
        )

    mapped_labs = [
        lab
        for index, module in enumerate(modules)
        for lab in _string_list(module, "labs", f"modules[{index}]")
    ]
    required_labs = _string_list(completion, "required_labs", "course_completion")
    if mapped_labs != required_labs:
        raise ValueError(f"required labs must match module order: {required_labs} != {mapped_labs}")
    if len(set(mapped_labs)) != len(mapped_labs):
        raise ValueError("each lab may appear only once")

    first_module = modules[0]
    if (
        first_module.get("id") != "postman-prerequisite"
        or first_module.get("prerequisite") is not True
        or mapped_labs[0] != "00-postman-prerequisite"
    ):
        raise ValueError("Postman prerequisite must be first and marked prerequisite: true")

    for lab in mapped_labs:
        guide = labs_root / lab / "README.md"
        if not guide.is_file():
            raise ValueError(f"missing lab guide: {guide}")

    return len(modules), module_hours, len(mapped_labs)


def main() -> int:
    try:
        module_count, hours, lab_count = validate_course_map(load_course_map())
    except (OSError, ValueError) as exc:
        print(f"course map invalid: {exc}")
        return 1

    print(f"course map OK ({module_count} modules, {hours} hours, {lab_count} labs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
