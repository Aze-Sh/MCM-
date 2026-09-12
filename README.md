# 2026 B 题：无线电干扰源定位与清除

本仓库按题目资料、两套算法和通用建模工具分类。第二套目前默认运行 v7；`adaptive` 是固定的方案目录名，以后升级版本也不需要再建“最新版”文件夹。

| 内容 | 入口 | 用途 |
| --- | --- | --- |
| 题目与附件 | [problem](problem/README.md) | 原始 PDF / Word、提取文本、任务分解、接口说明 |
| 第一套：覆盖扫描基线 | [solutions/baseline](solutions/baseline/README.md) | 当前 v3，含本地模拟器、演练记录、论文及冻结代码 |
| 第二套：自适应几何与任务规划 | [solutions/adaptive](solutions/adaptive/README.md) | 当前 v7，含可切换的早期策略、离线测试和论文 |
| 后续改进方向 | [docs/algorithm-development.md](docs/algorithm-development.md) | 定向信息、多源共享测点、成本界与参数验证 |
| 跳出固定覆盖点 | [docs/beyond-fixed-coverage.md](docs/beyond-fixed-coverage.md) | 按频道的信息状态规划、停止条件与可运行反例 |
| 逼近理论最优 | [docs/near-optimal-options.md](docs/near-optimal-options.md) | 四条候选路线的优缺点、最优性证书与独立下界 |
| 目录迁移与命名规则 | [docs/repository-layout.md](docs/repository-layout.md) | 旧路径对应关系、文件存放约定 |
| 通用建模工具箱 | [toolkit](toolkit/README.md) | Python / MATLAB 方法、模板、规则、检查器及 Skill 资源 |

以下命令从**仓库根目录**运行，Python 3.10+。

## 先运行第二套的离线检查

第二套运行代码和现有单元测试仅使用 Python 标准库：

```bash
python solutions/adaptive/run_tests.py
python solutions/adaptive/python/run_robot.py --help
```

默认策略是 `obligation-service-interception-v7`。连接模拟器的步骤见[运行说明](solutions/adaptive/docs/running.md)。第二套内部的 `--baseline` 指它自己的早期 midpoint 策略，**不等同于本仓库第一套方案**。

新增可选的 `--v8` 实验版：证据账本、保证完成的备用构造、事件前瞻、连续位置优化和有限世界精确校准已经接入。匹配测试中尚未稳定超过 v7，详见 [v8 实现与结果](solutions/adaptive/docs/v8-implementation.md)及[离线实验](experiments/near-optimal/README.md)。

## 运行第一套的本地模拟

```bash
python -m pip install -r solutions/baseline/python/requirements.txt pytest
python solutions/baseline/python/main.py simulate --cases 3 --seed 20260911
python scripts/check_repository.py
```

最后一条命令分进程运行两套方案现有的测试；它不会连接官方模拟器。第一套生成的报告在 `solutions/baseline/output/`。第二套连接运行后生成的目录在 `solutions/adaptive/results/runs/`。

## 使用通用工具箱

```bash
python -m pip install -e "./toolkit[test]"
python scripts/check_repository.py --suite all
```

`toolkit/` 保留原工具箱内部结构；它的文档命令通常要求先进入该目录。初始化模板用于新项目，不要对已有的两套方案执行强制初始化。

## 当前证据范围

第一套保留了六轮官方演练资料与历史合成测试。第二套上传说明提及早期版本演练和额外 v7 检查，但对应的完整原始记录没有一起上传；现有测试集中是 `test_offline.py`、`test_v4.py` 和 `test_v5.py`。论文中的历史数字、合成测试、官方演练和正式测试应分别注明来源。

此次整理保留两套算法的核心实现与参数、原始题目附件、论文和已有结果；入口路径及第二套默认输出目录已更新。

目录迁移后的 161 项现有 Python 测试已通过，核验范围见 [docs/layout-verification.json](docs/layout-verification.json)。新的探索脚本位于 [experiments/search-policy](experiments/search-policy/README.md)。
