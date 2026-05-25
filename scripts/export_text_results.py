import argparse
import json
import os
from datetime import datetime
from pathlib import Path


def read_accuracy_files(result_dir: Path):
    rows = []
    for path in sorted(result_dir.glob("*_accuracy.txt")):
        content = path.read_text(encoding="utf-8").strip()
        value = None
        if ":" in content:
            _, raw = content.split(":", 1)
            raw = raw.strip()
            try:
                value = float(raw)
            except ValueError:
                value = None
        rows.append(
            {
                "file": path.name,
                "content": content,
                "accuracy": value,
            }
        )
    return rows


def write_summary(export_dir: Path, split: str, checkpoint_dir: Path, result_dir: Path):
    export_dir.mkdir(parents=True, exist_ok=True)

    accuracy_rows = read_accuracy_files(result_dir)
    checkpoint_files = sorted(
        [p.name for p in checkpoint_dir.glob("*") if p.is_file()]
    ) if checkpoint_dir.exists() else []

    metadata = {
        "generated_at": datetime.now().isoformat(),
        "split": split,
        "checkpoint_dir": str(checkpoint_dir),
        "result_dir": str(result_dir),
        "checkpoint_exists": checkpoint_dir.exists(),
        "adapter_config_exists": (checkpoint_dir / "adapter_config.json").exists(),
        "adapter_model_exists": (checkpoint_dir / "adapter_model.bin").exists(),
        "checkpoint_files": checkpoint_files,
        "accuracy_files": accuracy_rows,
    }

    (export_dir / "summary.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        f"# triviaqa_{split} result summary",
        "",
        f"- generated_at: {metadata['generated_at']}",
        f"- checkpoint_dir: {checkpoint_dir}",
        f"- result_dir: {result_dir}",
        f"- adapter_config_exists: {metadata['adapter_config_exists']}",
        f"- adapter_model_exists: {metadata['adapter_model_exists']}",
        "",
        "## accuracy files",
        "",
    ]

    if accuracy_rows:
        for row in accuracy_rows:
            lines.append(
                f"- {row['file']}: {row['accuracy'] if row['accuracy'] is not None else row['content']}"
            )
    else:
        lines.append("- no accuracy files found")

    lines.extend(
        [
            "",
            "## checkpoint files",
            "",
        ]
    )

    if checkpoint_files:
        for name in checkpoint_files:
            lines.append(f"- {name}")
    else:
        lines.append("- no checkpoint files found")

    (export_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    raw_lines = []
    for row in accuracy_rows:
        raw_lines.append(f"{row['file']}\n{row['content']}\n")
    (export_dir / "accuracy_files.txt").write_text("".join(raw_lines), encoding="utf-8")

    print(f"Exported text summary to: {export_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_dir", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--checkpoint_dir", required=True)
    parser.add_argument("--split", required=True)
    parser.add_argument("--export_tag", default="")
    args = parser.parse_args()

    repo_dir = Path(args.repo_dir).resolve()
    export_tag = args.export_tag or f"triviaqa_{args.split}"
    export_dir = repo_dir / "analysis_exports" / export_tag
    result_dir = Path(args.out_dir).resolve() / "trivia_qa"
    checkpoint_dir = Path(args.checkpoint_dir).resolve()

    write_summary(export_dir, args.split, checkpoint_dir, result_dir)


if __name__ == "__main__":
    main()
