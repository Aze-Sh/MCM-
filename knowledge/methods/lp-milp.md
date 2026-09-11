# 线性与混合整数规划（lp-milp）

## 适用条件

目标和约束可线性表达，且包含容量、分配、选择、排产、库存或多期逻辑；离散决策用整数变量。

## 不适用条件

关键机理强非线性且线性化误差无法控制；变量/约束尚未定义完整时不要先写求解器代码。

## 数学定义

LP/MILP：最小化 (c^Tx)，满足 (Ax\le b, A_{eq}x=b_{eq}, l\le x\le u)，部分 (x_j\in\mathbb Z)。最优性由可行解、界和 gap 共同表征。

## 假设

系数确定或已通过情景/鲁棒形式表达；逻辑线性化和大 M 有有效紧界。

## 输入输出

输入目标、约束矩阵、界和整数索引；输出带状态、目标、变量、违约量和 gap 的结果对象。

## 选模理由

先做 LP 松弛给界，再加入必要整数逻辑；能用网络流或动态规划特化时优先更透明结构。

## Python 入口

`cumcm_py.optimization.solve_linear_program(c, A_ub=None, b_ub=None, bounds=None, integrality=None)`。

## MATLAB 入口

`cumcm.solveLinearProgram(model)`。

## 验证方法

手工小例/全枚举、独立重算目标和每类约束、LP 下界、求解 gap、尺度和大 M 敏感性、历史情景回放。

## 失败模式

索引错位；库存守恒漏期；整数解取整；大 M 过大；求解器超时仍称最优；目标量纲混合。

## 复杂度

LP 多项式可解；MILP 最坏指数级。利用稀疏性、紧界、对称破除和分解，限制比赛时间风险。

## 论文表达

先给集合/参数/变量表，再给目标和约束的业务解释；结果报告状态、gap、违约量和关键资源利用率。

## 来源

SciPy optimize、MATLAB Optimization 文档 `[PYDOC-SCIPY, MATLABDOC-OPTIMIZATION]`；案例 `[CUMCM-2021-C, CUMCM-2024-C]`。
