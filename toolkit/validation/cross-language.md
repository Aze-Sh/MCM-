# 跨语言验证状态

## 覆盖

- `code/fixtures/manifest.yaml` 为 13 个核心方法各登记一个手工可核对小夹具。
- 每项含输入 CSV、期望 JSON、比较属性、绝对/相对容差、种子和推导说明。
- `tools/compare_outputs.py` 对分类属性、路径/排名等精确比较，对数值数组按声明容差比较，并拒绝缺失属性。
- `tools/export_matlab_results.m` 统一 MATLAB 的 1 基索引和 camelCase 字段后再导出 JSON。

## 当前证据

- Python 比较器正/负/缺字段测试通过。
- 清单覆盖测试确认 13 个方法卡的 fixture ID 与共享清单完全一致。
- MATLAB R2024a 在普通 Windows 用户环境实际导出了全部 13 个夹具。
- 总清单比较实际检查 21 个声明属性，结果为 13 个夹具通过、0 个错误；机器可读报告为 `validation/cross-language-test-report.json`。

## 复现命令

```powershell
matlab -batch "addpath('code/matlab'); results=runtests('tests/matlab'); assertSuccess(results); run('tools/export_matlab_results.m')"
python tools/compare_outputs.py --expected-dir code/fixtures/expected --matlab-dir validation/output/matlab --manifest code/fixtures/manifest.yaml --json validation/cross-language-test-report.json
```

也可运行 `python tools/verify_repository.py --matlab auto --latex auto --json validation/repository-report.json` 一次完成 MATLAB 单测、导出和比较。可选工具箱缺失的 LP 项必须明确失败或跳过，不能使用旧输出写成通过。
