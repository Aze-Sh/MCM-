"""Return a minimal, prompt-sensitive resource route for the CUMCM Skill."""

from __future__ import annotations

import argparse
import json


ROUTES = {
    "implement-python": (["assets/code/python/cumcm_py"], ["implementation"]),
    "implement-matlab": (["assets/code/matlab/+cumcm"], ["implementation"]),
    "validate-results": (
        ["references/award-patterns/award-patterns.md", "references/methods/sensitivity-robustness.md"],
        ["result-validation"],
    ),
    "draft-structure": (
        ["references/writing/writing-and-figures.md", "assets/paper/main.tex"],
        ["writing-and-figures"],
    ),
    "check-submission": (
        ["references/compliance/2026-paper-format.md", "scripts/check_submission.py"],
        ["compliance", "final-packaging"],
    ),
    "record-ai-use": (
        ["assets/ai-usage/AI工具使用详情.md", "references/compliance/2026-ai-use.md"],
        ["compliance"],
    ),
}

PROBLEM_ROUTES = (
    (("预测", "时序", "forecast", "season"), "prediction", "time-series"),
    (("优化", "规划", "配送", "路径", "optimization"), "optimization", "lp-milp"),
    (("评价", "权重", "topsis", "evaluation"), "evaluation", "ahp-entropy-topsis"),
    (("机理", "微分", "动力", "ode", "mechan"), "mechanistic", "ode-difference"),
    (("网络", "图论", "network"), "network-spatial", "graph-flow-routing"),
    (("数据", "回归", "统计", "regression"), "data-analysis", "regression-inference"),
)


def route(intent: str, prompt: str = "") -> dict[str, object]:
    if intent in {"analyze-problem", "select-model"}:
        lowered = prompt.lower()
        problem_type, method = "data-analysis", "data-audit"
        for keywords, candidate_type, candidate_method in PROBLEM_ROUTES:
            if any(keyword in lowered for keyword in keywords):
                problem_type, method = candidate_type, candidate_method
                break
        resources = [
            f"references/problem-types/{problem_type}.md",
            f"references/methods/{method}.md",
        ]
        workflows = ["problem-intake", "model-selection"]
        if problem_type == "evaluation":
            workflows.append("result-validation")
    elif intent in ROUTES:
        resources, workflows = ROUTES[intent]
    else:
        raise ValueError(f"unsupported intent: {intent}")
    return {"intent": intent, "resources": list(resources), "workflows": list(workflows)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("intent")
    parser.add_argument("--prompt", default="")
    args = parser.parse_args()
    print(json.dumps(route(args.intent, args.prompt), ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
