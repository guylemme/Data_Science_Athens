"""Build an offline interactive HTML dashboard from computed analysis results."""
import argparse
import json
from pathlib import Path

from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parent


def build_dashboard(results_path=ROOT / "results/analysis.json", output_path=ROOT / "Soukaina_Bahami_dashboard.html"):
    """Input: analysis JSON and output path. Output: path of a self-contained HTML file.

    No CDN, remote map tiles, server or original CSV is needed to open the result.
    The input is JSON-encoded, never executed as source code.
    """
    results_path, output_path = Path(results_path), Path(output_path)
    results = json.loads(results_path.read_text(encoding="utf-8"))
    template = (ROOT / "dashboard/template.html").read_text(encoding="utf-8")
    payload = json.dumps(results, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    html = template.replace("/*__PLOTLY__*/", get_plotlyjs()).replace("/*__RESULTS__*/", payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main():
    """Input: CLI paths. Output: standalone dashboard written to disk."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results/analysis.json")
    parser.add_argument("--output", type=Path, default=ROOT / "Soukaina_Bahami_dashboard.html")
    args = parser.parse_args()
    print(build_dashboard(args.results, args.output))


if __name__ == "__main__":
    main()
