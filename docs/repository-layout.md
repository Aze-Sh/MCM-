# 目录布局与迁移说明

整理日期：2026-09-12；基于仓库提交 `dc34c1a`。目录按用途划分，版本号写入策略标识、说明和结果名称，不再用于命名“最新版”工作目录。

```text
MCM-/
├── README.md                    # 总导航、常用命令
├── problem/                     # 两套方案共用
│   ├── raw/                     # 题目 PDF、附件 Word 原件
│   ├── processed/               # 文本提取稿
│   ├── task-breakdown.md
│   └── simulator-interface.md
├── solutions/
│   ├── baseline/                # 第一套，当前 v3
│   │   ├── python/、matlab/、tests/
│   │   ├── paper/、figures/、figure-styles/
│   │   ├── output/、logs/、releases/
│   │   └── docs/                # 历史进度与准备清单
│   └── adaptive/                # 第二套，当前 v7
│       ├── python/、tests/
│       ├── paper/
│       ├── docs/                # 当前说明，history/ 存旧说明
│       ├── results/             # 新运行与整理后的证据
│       └── run_tests.py
├── docs/                        # 跨方案说明、改进路线、迁移核验
├── experiments/                 # 独立探索与可复现实例
├── scripts/check_repository.py  # 分别运行各套测试
└── toolkit/                     # 原通用工具箱，内部结构保留
```

## 旧路径对应关系

| 旧位置 | 新位置 |
| --- | --- |
| `contest/2026/` | `solutions/baseline/` |
| `contest/2026/data/` | `problem/` |
| `contest/2026/B题任务分解.md` | `problem/task-breakdown.md` |
| `contest/2026/模拟器接入说明.md` | `problem/simulator-interface.md` |
| `contest/2026/README.md` | `solutions/baseline/docs/progress-history.md`，另写当前首页 |
| `contest/2026/正式测试前检查清单.md` | `solutions/baseline/docs/preflight.md` |
| `contest/2026/check-report-*.json` | `solutions/baseline/output/checks/` |
| `最新版/代码/*.py` | `solutions/adaptive/python/`，测试除外 |
| `最新版/代码/test_*.py` | `solutions/adaptive/tests/` |
| `最新版/main.tex`、`main.pdf` | `solutions/adaptive/paper/` |
| `最新版/第七版创新与证据.md` | `solutions/adaptive/docs/v7-evidence.md` |
| `最新版/` 下的旧说明 | `solutions/adaptive/docs/history/`，新版操作指引为 `docs/running.md` |
| 两个 `shayebushi` 占位文件 | `solutions/adaptive/docs/history/unclassified/`，分别保留 |
| 原根目录 `code/`、`tests/`、`templates/` 等通用文件 | `toolkit/` 下的同名目录 |
| 原根目录 `pyproject.toml`、`README.md` | `toolkit/` 下，工具箱 README 更新使用位置 |
| 原 `docs/superpowers/` 开发计划 | `toolkit/docs/superpowers/`，作为历史记录保留 |

## 维护约定

- **代码**：在所属方案的 `python/` 修改。第二套早期版本模块仍被 v7 继承，不因名字较旧而移入归档。
- **测试**：放入所属方案 `tests/`。两套代码含有同名模块，应通过统一脚本分进程执行，避免导入互相污染。
- **文档**：当前算法与操作说明放方案 `docs/`，旧说明放 `docs/history/`；通用工具箱文档仍归 `toolkit/`。
- **结果**：第一套沿用 `output/` 与 `logs/`，第二套使用 `results/`。区分合成测试、演练和正式测试，记录版本、种子或案例编码。官方原始文件名保持不变。
- **论文**：所属方案 `paper/main.tex` 为源文件。发布快照单独冻结，不在冻结目录继续改代码。
- **命名**：目录、脚本采用稳定英文功能名；原始题目附件和具有明确含义的中文文件名保留。版本和日期用于实验记录、历史说明或冻结发布。

本次更新了实际入口、输出路径和活动清单。历史结果 JSON、动作日志及冻结发布内容中的旧绝对路径保留原文，避免改变证据与校验值；阅读历史路径时按上表定位。

通用工具箱移入子目录后，安装命令改为 `python -m pip install -e "./toolkit[test]"`；工具箱自己的命令从 `toolkit/` 内运行。两套方案的入口和测试命令见[仓库首页](../README.md)。
