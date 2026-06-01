#!/usr/bin/env python3
"""Post-hoc re-score saved TriviaQA generation outputs.

This script does not run models. It reads existing task.py JSON outputs and
recomputes accuracy under several answer-extraction modes.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Callable, Iterable


SPLITS = tuple(range(1, 11))

DATASETS = {
    "K_F": "test-forget_gold-answer_K-F",
    "K_S": "test-forget_sanitization-phrase_K-S",
    "K_R": "test-retrain_K-R",
}

SANITIZATION_DIRS = {
    1: Path("out/test_mb8_eval4_split1/triviaqa_1/results/trivia_qa"),
    2: Path("out/test_mb8_eval4_split1/triviaqa_2/results/trivia_qa"),
    3: Path("out/test_mb8_eval4_split1/triviaqa_3/results/trivia_qa"),
    4: Path("out/test_mb8_eval4_split1/triviaqa_4/results/trivia_qa"),
    5: Path("out/test_mb8_eval4_split1/triviaqa_5/results/trivia_qa"),
    6: Path("out/bs128_mb4_e20_kr1s2000_kr500_splits6_7_8_9_10_20260531_214718/triviaqa_6/results/trivia_qa"),
    7: Path("out/bs128_mb4_e20_kr1s2000_kr500_splits6_7_8_9_10_20260531_214718/triviaqa_7/results/trivia_qa"),
    8: Path("out/bs128_mb4_e20_kr1s2000_kr500_splits8_9_10_20260531_221921/triviaqa_8/results/trivia_qa"),
    9: Path("out/bs128_mb4_e20_kr1s2000_kr500_splits8_9_10_20260531_221921/triviaqa_9/results/trivia_qa"),
    10: Path("out/bs128_mb4_e20_kr1s2000_kr500_splits8_9_10_20260531_221921/triviaqa_10/results/trivia_qa"),
}

MODEL_NAMES = {
    "Orig": "no-lora",
    "Sanitization": "lora_sanitization",
}


@dataclass
class SplitScore:
    setting: str
    dataset: str
    mode: str
    split: int
    correct: int
    total: int
    path: str

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0


def exact_match(predicted_answer: str, task_output: Iterable[str]) -> int:
    outputs = list(task_output)
    if predicted_answer in outputs:
        return 1
    if predicted_answer.lower() in outputs:
        return 1

    if len(predicted_answer) >= 1:
        if predicted_answer[-1] == "." and predicted_answer[:-1] in outputs:
            return 1
        if predicted_answer[-1] == "." and predicted_answer[:-1].lower() in outputs:
            return 1
    return 0


def normalize_for_contains(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def contains_alias(predicted_answer: str, task_output: Iterable[str]) -> int:
    normalized_response = f" {normalize_for_contains(predicted_answer)} "
    for alias in task_output:
        normalized_alias = normalize_for_contains(alias)
        if not normalized_alias:
            continue
        if len(normalized_alias) == 1 and not normalized_alias.isdigit():
            continue
        if f" {normalized_alias} " in normalized_response:
            return 1
    return 0


def current_strict(response: str) -> str:
    return response.strip()


def first_line(response: str) -> str:
    return response.strip().splitlines()[0].strip() if response.strip() else ""


def before_next_instruction(response: str) -> str:
    return response.split("### Instruction:")[0].strip()


def paper_like(response: str) -> str:
    """Approximate paper-described TriviaQA answer extraction.

    The paper describes extracting generated answers by stopping at the first
    line break or final punctuation. For saved responses, we first cut at the
    first line break. If there is no line break, we cut at the last terminal
    punctuation mark when present.
    """
    stripped = response.strip()
    if not stripped:
        return ""

    line_match = re.search(r"[\r\n]", stripped)
    if line_match:
        return stripped[: line_match.start()].strip()

    punctuation_chars = ".!?:;" + "。！？；："
    last_punctuation = max(stripped.rfind(ch) for ch in punctuation_chars)
    if last_punctuation >= 0:
        return stripped[: last_punctuation + 1].strip()
    return stripped


EXTRACTORS: dict[str, Callable[[str], str]] = {
    "current_strict": current_strict,
    "first_line": first_line,
    "before_next_instruction": before_next_instruction,
    "paper_like": paper_like,
}

DIAGNOSTIC_MODES = ("contains_alias",)


def result_path(setting: str, split: int, dataset_name: str) -> Path:
    data_name = DATASETS[dataset_name]
    model_name = MODEL_NAMES[setting]
    filename = f"TASK-triviaqa_{split}_DATA-{data_name}_MODEL-{model_name}.json"
    if setting == "Orig":
        return Path(f"out/orig/triviaqa_{split}/results/trivia_qa") / filename
    if setting == "Sanitization":
        return SANITIZATION_DIRS[split] / filename
    raise ValueError(f"Unknown setting: {setting}")


def load_rows(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def score_rows(rows: list[dict], mode: str) -> tuple[int, int]:
    correct = 0
    for row in rows:
        response = row.get("model_response") or ""
        outputs = row.get("output") or []
        if mode == "contains_alias":
            correct += contains_alias(response, outputs)
        else:
            extracted = EXTRACTORS[mode](response)
            correct += exact_match(extracted, outputs)
    return correct, len(rows)


def collect_scores(settings: list[str], datasets: list[str]) -> list[SplitScore]:
    scores: list[SplitScore] = []
    for setting in settings:
        for dataset_name in datasets:
            for split in SPLITS:
                path = result_path(setting, split, dataset_name)
                if not path.exists():
                    continue
                rows = load_rows(path)
                for mode in list(EXTRACTORS) + list(DIAGNOSTIC_MODES):
                    correct, total = score_rows(rows, mode)
                    scores.append(
                        SplitScore(
                            setting=setting,
                            dataset=dataset_name,
                            mode=mode,
                            split=split,
                            correct=correct,
                            total=total,
                            path=str(path),
                        )
                    )
    return scores


def group_scores(scores: list[SplitScore]) -> dict[tuple[str, str, str], list[SplitScore]]:
    grouped: dict[tuple[str, str, str], list[SplitScore]] = {}
    for score in scores:
        grouped.setdefault((score.setting, score.dataset, score.mode), []).append(score)
    return grouped


def fmt_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def summarize(scores: list[SplitScore]) -> list[dict]:
    rows = []
    for (setting, dataset_name, mode), split_scores in sorted(group_scores(scores).items()):
        split_scores = sorted(split_scores, key=lambda item: item.split)
        macro = mean(score.accuracy for score in split_scores)
        correct = sum(score.correct for score in split_scores)
        total = sum(score.total for score in split_scores)
        rows.append(
            {
                "setting": setting,
                "dataset": dataset_name,
                "mode": mode,
                "macro": macro,
                "micro": correct / total if total else 0.0,
                "correct": correct,
                "total": total,
                "splits": {score.split: score.accuracy for score in split_scores},
            }
        )
    return rows


def response_length_stats(settings: list[str]) -> list[dict]:
    stats = []
    for setting in settings:
        for dataset_name in ("K_F", "K_S"):
            lengths = []
            newline_count = 0
            instruction_count = 0
            for split in SPLITS:
                path = result_path(setting, split, dataset_name)
                if not path.exists():
                    continue
                for row in load_rows(path):
                    response = row.get("model_response") or ""
                    lengths.append(len(response))
                    if "\n" in response:
                        newline_count += 1
                    if "### Instruction:" in response:
                        instruction_count += 1
            if lengths:
                stats.append(
                    {
                        "setting": setting,
                        "dataset": dataset_name,
                        "count": len(lengths),
                        "avg_chars": sum(lengths) / len(lengths),
                        "max_chars": max(lengths),
                        "newline_rate": newline_count / len(lengths),
                        "instruction_rate": instruction_count / len(lengths),
                    }
                )
    return stats


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_markdown(output_path: Path, scores: list[SplitScore], summary_rows: list[dict], length_stats: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    focus_rows = []
    for setting in ("Orig", "Sanitization"):
        for dataset_name in ("K_F", "K_S", "K_R"):
            for mode in ("current_strict", "first_line", "before_next_instruction", "paper_like", "contains_alias"):
                match = next(
                    (
                        row
                        for row in summary_rows
                        if row["setting"] == setting and row["dataset"] == dataset_name and row["mode"] == mode
                    ),
                    None,
                )
                if not match:
                    continue
                focus_rows.append(
                    [
                        setting,
                        dataset_name,
                        mode,
                        fmt_pct(match["macro"]),
                        fmt_pct(match["micro"]),
                        f'{match["correct"]}/{match["total"]}',
                    ]
                )

    split_rows = []
    for split in SPLITS:
        row = [str(split)]
        for setting, dataset_name, mode in [
            ("Orig", "K_F", "current_strict"),
            ("Orig", "K_F", "paper_like"),
            ("Orig", "K_F", "contains_alias"),
            ("Sanitization", "K_F", "current_strict"),
            ("Sanitization", "K_F", "paper_like"),
            ("Sanitization", "K_S", "current_strict"),
            ("Sanitization", "K_S", "paper_like"),
        ]:
            score = next(
                (
                    item
                    for item in scores
                    if item.setting == setting and item.dataset == dataset_name and item.mode == mode and item.split == split
                ),
                None,
            )
            row.append(fmt_pct(score.accuracy) if score else "n/a")
        split_rows.append(row)

    length_rows = [
        [
            row["setting"],
            row["dataset"],
            str(row["count"]),
            f'{row["avg_chars"]:.1f}',
            str(row["max_chars"]),
            fmt_pct(row["newline_rate"]),
            fmt_pct(row["instruction_rate"]),
        ]
        for row in length_stats
    ]

    output_path.write_text(
        "\n".join(
            [
                "# TriviaQA 输出重评分分析",
                "",
                "本文件由 `scripts/rescore_triviaqa_outputs.py` 生成。",
                "脚本只读取已经保存的 JSON 输出重新计分，不运行模型推理。",
                "",
                "## 抽取口径",
                "",
                "- `current_strict`：直接使用保存的 `model_response`，对应当前 `task.py` 行为。",
                "- `first_line`：只保留第一处换行前的文本。",
                "- `before_next_instruction`：截断到下一个 `### Instruction:` 标记前。",
                "- `paper_like`：近似论文描述的 TriviaQA 抽取方式，优先按第一处换行截断，否则按最后一个终止标点截断。",
                "- `contains_alias`：仅用于诊断；只要任一标准化 gold alias 出现在 response 中就计为命中。",
                "",
                "## 汇总",
                "",
                markdown_table(
                    ["Setting", "Dataset", "Mode", "Macro", "Micro", "Correct/Total"],
                    focus_rows,
                ),
                "",
                "## Split 级重点对比",
                "",
                markdown_table(
                    [
                        "Split",
                        "Orig K_F strict",
                        "Orig K_F paper_like",
                        "Orig K_F contains",
                        "Sani K_F strict",
                        "Sani K_F paper_like",
                        "Sani K_S strict",
                        "Sani K_S paper_like",
                    ],
                    split_rows,
                ),
                "",
                "## 输出长度与续写诊断",
                "",
                markdown_table(
                    ["Setting", "Dataset", "N", "Avg chars", "Max chars", "Has newline", "Has `### Instruction:`"],
                    length_rows,
                ),
                "",
                "## 解释说明",
                "",
                "- Orig `K_F` strict exact-match 不能可靠估计答案泄露，因为很多 response 是先输出短答案，再继续续写 prompt。",
                "- `contains_alias` 故意放宽，只能作为泄露诊断，不能当作正式论文指标。",
                "- `paper_like` 比当前 strict matching 更接近论文描述，但仍然是基于已有生成结果的 post-hoc 近似。",
                "- 如果 Sanitization 在 `paper_like` 下仍明显低于论文结果，那么复现差距不能只由 answer extraction 解释。",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_json(output_path: Path, summary_rows: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary_rows, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="docs/rescore-analysis.md", help="Markdown output path.")
    parser.add_argument("--json-output", default="docs/rescore-analysis.json", help="Machine-readable summary path.")
    parser.add_argument(
        "--settings",
        nargs="+",
        default=["Orig", "Sanitization"],
        choices=["Orig", "Sanitization"],
        help="Which saved settings to score.",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["K_F", "K_S", "K_R"],
        choices=["K_F", "K_S", "K_R"],
        help="Which datasets to score when files exist.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scores = collect_scores(args.settings, args.datasets)
    summary_rows = summarize(scores)
    length_stats = response_length_stats(args.settings)
    write_markdown(Path(args.output), scores, summary_rows, length_stats)
    write_json(Path(args.json_output), summary_rows)
    print(f"Wrote {args.output}")
    print(f"Wrote {args.json_output}")


if __name__ == "__main__":
    main()
