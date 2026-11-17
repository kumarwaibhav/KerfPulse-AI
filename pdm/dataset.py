"""Acquire the versioned cutter benchmark and create a causal reading stream."""

import argparse
import csv
import hashlib
import io
import json
import math
import os
import tempfile
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


SOURCE_VERSION = "10.6084/m9.figshare.28589216.v1"
SOURCE_URL = "https://ndownloader.figshare.com/files/52968974"
SOURCE_SHA256 = "e125471f983e98ae326e2c47e15f633bb30738e285b9ad6e54b5e364d4d66dbc"
SOURCE_MD5 = "cbcad3f9631e0be6c4f71ff27749108c"
SOURCE_SIZE = 1_797_280
SOURCE_NAME = "FeatureAndMetadata_Milling.csv"
RECIPE_FIELDS = ("MillingToolType", "ADOC", "RDOC", "ToolHolderLength")
NUMERIC_CONTEXT = ("NumberOfCycle", "HardnessMean", *RECIPE_FIELDS)


class DatasetError(ValueError):
    """Dataset unavailable or different from the pinned publication."""


@dataclass(frozen=True)
class Cut:
    tool_id: int
    cycle: int
    recipe: tuple[float, ...]
    context: dict[str, float]
    current: dict[str, float]
    vibration: dict[str, float]
    status: str


@dataclass(frozen=True)
class Tool:
    id: int
    cuts: tuple[Cut, ...]
    failure_cycle: int
    workpieces: frozenset[str]

    @property
    def recipe(self) -> tuple[float, ...]:
        return self.cuts[-1].recipe


def source_path() -> Path:
    return Path(os.getenv("PDM_DATA_DIR", "data")) / SOURCE_NAME


def verify_source(content: bytes) -> None:
    if len(content) != SOURCE_SIZE or hashlib.sha256(content).hexdigest() != SOURCE_SHA256:
        raise DatasetError(f"CSV does not match Figshare {SOURCE_VERSION}")


def fetch() -> Path:
    path = source_path()
    if path.exists():
        verify_source(path.read_bytes())
        return path
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "cnc-pdm-replay/1.0"})
    with urllib.request.urlopen(request, timeout=40) as response:
        content = response.read(SOURCE_SIZE + 1)
    verify_source(content)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as file:
        temporary = Path(file.name)
        file.write(content)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def number(value: str) -> float:
    result = float(value.replace(",", "."))
    if not math.isfinite(result):
        raise DatasetError("Non-finite numeric value in source CSV")
    return result


@lru_cache(maxsize=1)
def read(source: Path) -> dict[int, Tool]:
    try:
        content = source.read_bytes()
    except FileNotFoundError as exc:
        raise DatasetError("Dataset is missing. Run python -m pdm.dataset fetch") from exc
    verify_source(content)
    stream = io.StringIO(content.decode("utf-8-sig"))
    next(stream)  # Figshare export includes a generic header ahead of field names.
    reader = csv.DictReader(stream, delimiter=";")
    fields = reader.fieldnames or []
    current_fields = tuple(name for name in fields if name.startswith("Current - "))
    vibration_fields = tuple(name for name in fields if name.startswith("Accelerometer - "))
    if (len(fields), len(current_fields), len(vibration_fields)) != (131, 72, 48):
        raise DatasetError("Unexpected dataset field contract")

    rows = defaultdict(lambda: defaultdict(list))
    for row in reader:
        rows[int(row["TollIndex"])][int(row["NumberOfCycle"])].append(row)

    tools = {}
    for tool_id, by_cycle in sorted(rows.items()):
        failure_cycles = {
            cycle + int(row["CycleToFailure"])
            for cycle, records in by_cycle.items()
            for row in records
        }
        failure = max(by_cycle)
        if failure_cycles != {failure} or len(by_cycle[failure]) != 1:
            raise DatasetError(f"Inconsistent damage endpoint for cutter {tool_id}")
        terminal = by_cycle[failure][0]
        recipe = tuple(number(terminal[field]) for field in RECIPE_FIELDS)
        cuts = []
        for cycle in range(1, failure + 1):
            records = by_cycle.get(cycle, ())
            if cycle == failure:
                cuts.append(Cut(tool_id, cycle, recipe, {}, {}, {}, "damage"))
            elif len(records) != 1:
                quality = "conflict" if records else "gap"
                cuts.append(Cut(tool_id, cycle, recipe, {}, {}, {}, quality))
            else:
                row = records[0]
                context = {field: number(row[field]) for field in NUMERIC_CONTEXT}
                observed_recipe = tuple(context[field] for field in RECIPE_FIELDS)
                if observed_recipe != recipe:
                    raise DatasetError(f"Cutter {tool_id} has inconsistent recipe metadata")
                current = {field: number(row[field]) for field in current_fields}
                vibration = {field: number(row[field]) for field in vibration_fields}
                cuts.append(Cut(tool_id, cycle, recipe, context, current, vibration, "ok"))
        workpieces = frozenset(row["SampleIndex"] for records in by_cycle.values() for row in records)
        tools[tool_id] = Tool(tool_id, tuple(cuts), failure, workpieces)
    return tools


def load() -> dict[int, Tool]:
    return read(source_path().resolve())


def list_tools() -> list[dict]:
    return [
        {
            "tool_id": tool.id,
            "cycles": len(tool.cuts),
            "recorded_cuts": sum(cut.status == "ok" for cut in tool.cuts),
            "recipe": dict(zip(RECIPE_FIELDS, tool.recipe)),
        }
        for tool in load().values()
    ]


def audit() -> dict:
    tools = load()
    cuts = [cut for tool in tools.values() for cut in tool.cuts]
    return {
        "doi": SOURCE_VERSION,
        "source_bytes": SOURCE_SIZE,
        "source_rows": 968,
        "sha256": SOURCE_SHA256,
        "md5": SOURCE_MD5,
        "tools": len(tools),
        "recipes": len({tool.recipe for tool in tools.values()}),
        "eligible_pre_damage_cuts": sum(cut.status == "ok" for cut in cuts),
        "missing_ordinals": sum(cut.status == "gap" for cut in cuts),
        "conflicting_ordinals": sum(cut.status == "conflict" for cut in cuts),
        "quarantined_rows": 2,
        "first_cut_damage_tools": [tool.id for tool in tools.values() if tool.failure_cycle == 1],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("fetch", "audit"))
    args = parser.parse_args()
    if args.command == "fetch":
        print(fetch())
    print(json.dumps(audit(), indent=2))


if __name__ == "__main__":
    main()
