# 保留的验证数据

这里只保留最终版本的输入、回归依据、完整日志和必要结果摘要。

| 文件/目录 | 内容 |
|---|---|
| `expected-fast.json` | 按已发布提交固定的30场源真值、噪声配置、用时、操作次数和请求指纹；仅模拟器/核查器可用 |
| `recorded/` | 整理后对相同30场重跑的结果、完整协议日志及独立审计 |
| `migration.json` | 主算法、几何、协议及抽取依赖的函数体核对与前后文件哈希 |
| `file-mapping.json` | 主要旧文件与新文件的对应关系 |
| `test-summary.json`、`tests.txt` | 上一次目录整理时48项测试的结果和输出 |
| `style-refactor.json` | 本次代码风格整理的规模、源码哈希、测试和整场回归摘要 |
| `materials-sha256.json`、`questions-check.json` | 题目/论文原件哈希及第一二题新旧入口输出核对 |
| `cleanup-summary.json` | 清理规模、选定提交及仓库外备份信息 |
| `performance-comparison.json` | 选定快速版相对v7的20场同输入历史性能摘要 |
| `input-inventory.json` | 用户十份加密官方演练附件的安全元数据与截图对应；不包含解密内容 |

```bash
python tools/validate.py --output runs/style-check
python tools/validate.py --verify-only --output runs/style-check
```

`recorded/` 保留上一次目录整理的原始记录；其源码哈希对应当时的版本。本次完整输出保存在被Git忽略的 `runs/style-20260913/`，可用上述命令复现到新目录。

这些命令核对现有源码、日志、真实计费和全清依据。修改源码后，如哈希不一致，应在新的 `runs/` 目录重跑，不要手工修改历史哈希或覆盖原验证结论。

求解器从不接收这里保存的源真值。真值仅由本地模拟器用于产生协议返回，由核查器用于验证实际清除。
