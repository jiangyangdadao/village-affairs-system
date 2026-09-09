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
| 部署 | 村内 Windows 10/11 电脑，一键安装 exe，开机自启 |
| 访问 | 局域网（手机连村 WiFi），管理入口二维码，固定 IP + 海报 |
| 数据 | SQLite 单文件 + 本地附件，每日自动备份 30 份 |
| 权限 | 仅工作人员：管理密码登录，电脑端全功能、手机端仅查看 |
| 授权 | 30 天试用 + 机器绑定激活码离线解锁；到期数据保留、可全量导出 |
| 技术 | Python FastAPI + SQLite + Vue3(Vant) + openpyxl + reportlab |
| 远程运维 | 安装包发微信 + 向日葵远程协助 |

## 状态

设计已按新需求调整为仅工作人员版（2026-09-09），UI 效果图待审阅，开发实施计划待编写。

> 页面中所有人物、村名、数字均为虚构示例。
