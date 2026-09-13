# v8快速版的验证与成绩范围

## 本次保留哪个版本

保留已发布的提交 `8b2d232b5297976bee682be718f617f19dfbbd23`，内部标识为 **`20260912-shared-service-r4`**。后续本地r5未采用。目录与代码风格整理均以该快速版为基础。接口和文件组织的变化见 [代码整理说明](code_style.md)。

## 快速版原有性能证据

该版本已有20场相同源位置、半径、朝向、频道与噪声的v7对照：19场更快，13场节省至少500秒；另有1场Q4回退约184秒。不能把这些合成场景统计理解成所有实际案例的保证。

各场数字保留在 [performance-comparison.json](../validation/performance-comparison.json)。原始历史日志仍可由Git历史或仓库外备份恢复，当前目录不再保留反复调参、失败原型和重复旧结果。后续r5所报告的“平均省约57秒、最大省约211秒”不属于本次选定版本的新增收益。

## 目录整理的回归标准

以该已发布快速版的30场结果固定 [expected-fast.json](../validation/expected-fast.json)，其中包含4场固定、8场验证、8场保留输入、8场边界/密集压力、2场备用完成案例。记录源真值、噪声配置、虚拟用时、操作次数和完整协议请求指纹。

整理后重新运行同样30场，并检查：

- 实际源全部清除，正常退出；证据日志回放通过。
- 每条协议请求的路径和内容指纹与选定快速版一致，总虚拟用时和操作次数一致。
- 运行源码及日志哈希匹配；没有把旧日志改个版本号当成新运行。
- 所有实际完整光学链通过连续覆盖、额度、整个事件预算和成功前缀核查。

新日志与报告保留在 [validation/recorded](../validation/recorded/)，主报告为 [verification.json](../validation/recorded/verification.json)。这些是上一次目录整理时的记录，源码哈希对应提交 `fae3c1a`。本次风格整理的新结果见 [style-refactor.json](../validation/style-refactor.json)；用 `python tools/validate.py --output runs/style-check` 生成当前源码的完整记录，再用 `--verify-only --output runs/style-check` 核查。

当前相关测试用 `python check.py` 运行。旧策略、未选用r5的专项测试和通用工具库测试随对应实现移除；不沿用此前大仓库205项测试的数量。上一次精简版包含48项测试；本次更新为49项测试，取消重试测试，增加单次HTTP交互和异常直接抛出检查，继续覆盖当前算法、协议、默认启动、几何、预算、全清和离线超时。

## 用户提供的十场官方演练

截图顺序已由用户确认，可与 `.jlog` 公开头部时间对应。必要元数据和文件SHA256保留在 [input-inventory.json](../validation/input-inventory.json)。正文为 `aes-256-gcm-chunked` 加密，目前没有解出动作、真实源布局或精确总用时。

当前离线结果不能冒充这十场的复测。逐阶段分析需要同次运行的机器人侧 `actions.jsonl`、`summary.json` 和 `metadata.json`；它们也未必足以反推出全部源参数。

本次整理只进行离线模拟，没有启动或连接官方模拟器，也没有正式测试。该版尚未证明接近理论最优，稳定比v7省500秒的目标仍未完成。
