# 村务管理系统（单村局域网版）

为村级组织设计的轻量村务数据系统：村务工作人员在村办公室电脑上维护台账，并用手机浏览器随时查看，数据全部保存在村内电脑，**不上传任何云端服务器**。

## 核心特性

- **一次录入、处处复用**：户、人只录一次身份证，11 类台账自动关联，户情报告自动聚合生成
- **手机随时查看**：工作人员手机随时查看全部台账，与电脑端数据一致；电脑端负责增删改与导入导出
- **零门槛部署**：一键安装 exe、双击启动、复制文件夹即备份
- **中国红党政风格界面**：九宫格管理首页，红金配色

## 设计资料（网页版入口）

入口页：https://jiangyangdadao.github.io/village-affairs-system/

- 🖥 [UI 效果图（网页版）](https://jiangyangdadao.github.io/village-affairs-system/%E6%9D%91%E5%8A%A1%E7%AE%A1%E7%90%86%E7%B3%BB%E7%BB%9F-UI%E6%95%88%E6%9E%9C%E5%9B%BE.html) —— 8 个关键界面，中国红党政风格
- 📄 [UI 效果图（PDF 版）](https://jiangyangdadao.github.io/village-affairs-system/%E6%9D%91%E5%8A%A1%E7%AE%A1%E7%90%86%E7%B3%BB%E7%BB%9F-UI%E6%95%88%E6%9E%9C%E5%9B%BE.pdf) —— 微信可直接转发
- 📐 [设计方案（网页版）](https://jiangyangdadao.github.io/village-affairs-system/%E6%9D%91%E5%8A%A1%E7%AE%A1%E7%90%86%E7%B3%BB%E7%BB%9F%E8%AE%BE%E8%AE%A1%E6%96%B9%E6%A1%88.html) —— 架构 / 数据库 / 权限 / 流程 / 部署

## 文档目录

```
docs/
├── index.html                        # Pages 首页（设计资料导航）
├── 村务管理系统-UI效果图.html          # UI 效果图（11 屏，红金党政风格）
├── 村务管理系统-UI效果图.pdf           # UI 效果图 PDF 版
├── 村务管理系统设计方案.html            # 设计方案网页版
└── superpowers/specs/
    └── 2026-09-07-村务管理系统-design.md   # 设计方案 Markdown 源稿（12 章）
```

## 设计要点速览

| 项 | 结论 |
|---|---|
| 部署 | 村内电脑，Windows 一键安装 exe（macOS .app 可选），开机自启 |
| 访问 | 局域网（手机连村 WiFi），管理入口二维码，固定 IP + 海报 |
| 数据 | SQLite 单文件 + 本地附件，每日自动备份 30 份 |
| 权限 | 仅工作人员：管理密码登录，电脑端全功能、手机端仅查看 |
| 授权 | 30 天试用 + 机器绑定激活码离线解锁；到期数据保留、可全量导出 |
| 技术 | Python FastAPI + SQLite + Vue3(Vant) + openpyxl + reportlab |
| 远程运维 | 安装包发微信 + 向日葵远程协助 |

## 状态

实现完成，端到端验收记录于 2026-09-09（feature/implementation 分支，可交付产物 tag `v0.1.2`）。

**本机可执行验收（已通过）**

| 项 | 结果 |
|---|---|
| 后端全量测试 | 56 passed（`backend/.venv/bin/python -m pytest app/tests/ -q`） |
| 前端构建 | 成功（Vite 317 模块 → `backend/web`） |
| API 冒烟链路 | 登录 → 建台账 → 列表 → 模板下载 → 导入（1 行错误被准确报出行号 4 与原因，其余入库）→ 户情报告 PDF（%PDF，收入汇总与台账一致）→ 二维码 PNG → 海报 PDF → 授权状态 → 统计 → 操作日志（新增/导入/备份/删除齐全、可按模块/类型筛选）→ 备份 zip → 删除留痕，全程 200 |
| 11 类台账演练 | 全部 create=200 / edit=200 / delete=200，且每类均有新增/编辑/删除操作日志 |
| 手机只读边界 | LedgerList/LedgerDetail/LedgerEdit 全部写入口（新增/编辑/删除/导入导出/附件上传）均在 `!isMobile()` 守卫内，手机端仅提示到电脑端操作（静态检查） |
| 安全拦截 | 未登录访问受保护 API 返回 401；登录/授权状态/激活/全量导出白名单正常放行 |
| 授权（静态+单测） | `license.check()` 含时间回拨分支（`now < last` → tampered 锁定）；`test_tampered_state_locks_without_reset` 通过；签发脚本 `deploy/scripts/gen_activation_code.py` 与 `license.make_activation_code` 对同一指纹输出一致 |
| CI | tag `v0.1.2` → run 34364266141 双平台 success（Windows ~1m43s / macOS ~53s），产物平铺布局已校验 |

**待人工演练（需真实环境，交付时执行）**

- Windows 虚拟机一键安装演练：安装.bat、开机自启、防火墙放行、时间回拨实测、删除 data 目录、备份恢复（`deploy/windows/`）
- macOS 安装演练：Gatekeeper 右键打开、LaunchAgent 自启（`deploy/macos/`）
- 真实 Android/iPhone 手机浏览器访问（手机只读边界实机确认）
- 真实机器激活码签发 → 输入 → 解锁全流程（本机已完成签发一致性自测）
- 九宫格与各页面 UI 浏览器点击走查（17 宫格路由已静态确认，实际浏览器交互待人工）

> 页面中所有人物、村名、数字均为虚构示例。
