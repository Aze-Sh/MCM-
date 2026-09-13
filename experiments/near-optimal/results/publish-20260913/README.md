# 2026-09-13 提交前兼容核验

本次将提速版 `20260912-shared-service-r4` 合并到远端提交 `900cd56` 之后，保留其 Windows 离线模拟超时检查。主策略四个文件没有变化；模拟器保持关闭，全部核验均为离线操作。

- Windows 超时测试两项通过，合并后的模拟脚本通过 F 类静态检查。
- `current-matched/` 保存合并后重跑的四场固定案例。均实际全清、正常退出、回放通过，用时与 r4 原记录一致，727 条请求的路径和正文逐条一致。
- `pre-merge-verification.json` 保存合并前的验证报告，以保留当时的模拟脚本哈希。合并后的完整复核报告仍位于 `../optimization-20260912/round4/verification.json`。
- 合并后重新完成30份当前轨迹、14份历史轨迹及62条光学链核查，源码和日志哈希均通过。本目录 `verification.json` 汇总提交前检查；测试在Linux执行，不冒充原生Windows运行结果。
- 完整用时对照和未达到500秒要求的案例见 [v8 提速说明](../../../../solutions/adaptive/docs/v8-optimization.md)。这次 GitHub 提交不表示原性能目标已经完成。
