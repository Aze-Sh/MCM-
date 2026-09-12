# B题正式测试冻结版 v3

冻结时间：2026-09-11 11:08（北京时间）。策略标识：`coverage600-nearest-resume-adaptive8-grid20-stop16-v3`。

本目录的 `code/` 是正式测试候选代码快照。源代码已经通过29项B题专项测试、86项仓库测试和同种子100局合成压力测试；问题3、4各完成3轮官方演练，累计清除82/82。不要在正式测试轮次之间直接修改此快照。

正式入口必须同时提供题号、该题正式轮次和 `--confirm-formal`。参赛队号通过环境变量输入，不写入代码。示例仅展示问题3第1轮；只有在模拟器明确显示对应正式测试“等待机器狗进入”、队伍完成最终核对并授权后才能执行：

```powershell
Set-Location C:\Users\37828\Desktop\国赛
$env:CUMCM_ROBOT_ID = Read-Host '请输入当前登录参赛队号'
python -X utf8 `
  contest\2026\releases\formal-v3-20260911\code\main.py formal `
  --problem 3 --formal-run 1 --confirm-formal `
  --output contest\2026\releases\formal-v3-20260911\output\formal-q3-run1.json
```

每轮结束后先确认模拟器显示正常结束与上传完成，再按原文件名备份 `.jlog`、`.psum`、`.result.json`，随后更新 `result-manifest.yaml`。正式测试启动或中止都会消耗次数。
