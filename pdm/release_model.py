"""Build a single engineering release, keeping cutters 2 and 4 out of training."""
import hashlib
import json
import platform
from pathlib import Path
import sklearn

from pdm.dataset import SOURCE_SHA256, load
from pdm.train import feature_names
from pdm.validation import fit


def main():
    tools = load()
    training_tools = [tool for tool in tools.values() if tool.id not in (2, 4) and any(cut.status == "ok" for cut in tool.cuts)]
    rows = [(cut, tool.failure_cycle - cut.cycle) for tool in training_tools
            for cut in tool.cuts if cut.status == "ok"]
    names = feature_names(rows[0][0], "current")
    model = fit(rows, names, 0.01)
    payload = {"features": names, "classes": model.classes_.tolist(), "mean": model[0].mean_.tolist(),
               "scale": model[0].scale_.tolist(), "coef": model[-1].coef_.tolist(),
               "intercept": model[-1].intercept_.tolist(), "temperature": 1.0}
    directory = Path("artifacts/engineering-release")
    directory.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, allow_nan=False).encode()
    (directory / "model.json").write_bytes(encoded)
    manifest = {"release": "haas-current-engineering-v1", "digest": hashlib.sha256(encoded).hexdigest(),
                "source_sha256": SOURCE_SHA256, "training_tools": sorted(tool.id for tool in training_tools), "excluded_tools": [2, 4],
                "eligible_training_rows": len(rows), "no_eligible_rows_tools": [tool.id for tool in tools.values() if not any(cut.status == "ok" for cut in tool.cuts)],
                "build": {"python": platform.python_version(), "scikit_learn": sklearn.__version__, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
                "feature_schema_version": "haas-cut-summary-v1", "sensor_profile_version": "piecuch-haas-vf1-summary-v1",
                "supported_recipes": [list(recipe) for recipe in sorted({tool.recipe for tool in training_tools})],
                "calibration_status": "benchmark estimate; plant calibration pending", "approval": "engineering demonstration only",
                "parameters": {"C": 0.01, "selection": "fixed from previously recorded baseline; reused benchmark is development evidence"},
                "target": "published cutter damage", "horizon": "1..8 further cuts and greater than 8", "predecessor": None}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
