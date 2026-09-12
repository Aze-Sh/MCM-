> 这是迁移前的开发记录，保留当时的进度与命令。当前路径和运行方法见 [方案首页](../README.md)。文中 `contest/2026/` 现为 `solutions/baseline/`，原 `data/` 现为仓库根目录 `problem/`。

# 数学建模项目

已选择 **B 题：无线电干扰源的快速自动定位与清除**。先读 [B题任务分解](../../../problem/task-breakdown.md) 和 [模拟器接入说明](../../../problem/simulator-interface.md)，原始题面在 `data/raw/B题.pdf`，附件 1、附件 2 已归档到 `data/raw/B题附件/`。问题 3、4 已各完成三轮官方演练，六轮累计清除 82/82；正式测试尚未启动。

本地合成模拟已完成 100 局（问题 3、4 各 50 局），全部清除成功；结果仅用于代码回归，不是官方成绩，见 `output/synthetic-stress-20260911.json`。六轮官方演练的逐轮报告和原始行为文件均保存在 `logs/official-practice/` 与 `output/official-practice-*.json`。

当前论文工作稿共 18 页、8 幅图，已经加入问题二参数敏感性、问题三四策略消融、问题四定向比例压力分析和模型评价；正式结果表仍为空，见 `paper/main.pdf`。

首次演练使用 v1 策略。当前待演练的 v2 保留同一覆盖点集合，在定位清除后改从最近的未完成覆盖点继续；同种子 100 局合成对照仍全部清除，问题 3、4 平均虚拟时间分别下降 12.70% 和 9.99%，见 `output/synthetic-stress-route-v2-20260911.json`。

v2 已完成第二次问题 3 官方演练：案例 `FYKN-VY2Y-C99F-6BZN` 共 15 个全向源，清除 15 个，虚拟总时间 16696.588548 秒，平均定位清除时间 1113.105903 秒，515 条请求全部接受。首次问题 4 官方演练也已完成：案例 `77QS-523V-UX4E-UCGC` 共 14 个源（全向 11、定向 3），全部清除，虚拟总时间 15927.931031 秒，583 条请求全部接受。当前仍未启动任何正式测试。

第二次问题 4 官方演练案例 `UC47-56D3-EHEC-RTK3` 共 16 个源（全向 7、定向 9），清除 16/16，虚拟总时间 17598.383071 秒，525 条请求全部接受。四次官方演练累计清除 56/56；问题 4 两局共清除 12 个定向源。当前仍未启动任何正式测试。

当前冻结策略为 v3：清除达到题面上限16个后立即结束。相同100局合成回归全部清除，16源案例中问题3、4平均虚拟时间相对v2分别下降32.59%和19.60%。正式候选代码见 `releases/formal-v3-20260911/code/`。

v3第三次问题4官方演练案例 `F6QC-7NFR-B6ES-WJMF` 共11个源（全向5、定向6），清除11/11，虚拟总时间16538.538737秒；本局验证了少于16源时完成全部覆盖再退出的分支。三次问题4演练累计清除41/41，其中定向源18个。

v3第三次问题3官方演练案例 `8BS5-GQWW-6BTJ-8Z73` 共15个全向源，清除15/15，虚拟总时间16282.901650秒，516条请求全部接受。问题3、4各完成三轮官方演练，六轮累计清除82/82；当前仍未启动正式测试。

## 一条命令

- Python：`python python/main.py`
- MATLAB：`matlab -batch "run('matlab/main.m')"`

原始数据只放 `data/raw/`，不要在脚本中使用绝对路径。结果统一写入 `output/`，图片写入 `figures/`，并更新 `result-manifest.yaml`。

比赛中对本目录运行 `--stage draft`。提交前将最终论文 PDF、`AI工具使用详情.pdf`（如使用 AI）和运行入口复制到单独的最终打包目录（顶层论文、AI 详情文件和 `code/main.py` 或 `code/main.m`），再对打包目录运行 `--stage submission`；不要直接把本工作目录当作上传包。

## 官方问题 3 演练

确认模拟器界面当前选中“问题 3 演练测试”并显示接口已就绪后，再在 PowerShell 中运行：

```powershell
Set-Location C:\Users\37828\Desktop\国赛
$env:CUMCM_ROBOT_ID = Read-Host '请输入当前登录参赛队号'
$runStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
python -X utf8 contest\2026\python\main.py practice --problem 3 --confirm-practice `
  --output "C:\Users\37828\Desktop\国赛\contest\2026\output\official-practice-q3-$runStamp.json"
```

程序会先调用 `/enter`，按覆盖基线运行，再调用 `/exit`，动作与响应记录在 `contest/2026/logs/`。若接口未就绪、队号不匹配或返回不确定错误，程序会停止并保留原请求；不要改用新的 request_id 重复发送同一个未确认动作。正式测试不要使用此命令。
