# CombatLens

Build a reusable local research tool for action-game players and combat designers.
Read `ETHAN.md`, `docs/STATUS.md` and the current OpenSpec change before editing.
Natural-language requests route through registered adapters. Do not label imported
research as newly unpacked data. Preserve native IDs, units and source evidence.

Public Git contains generic code, contracts, synthetic tests and third-party
notices. Game-specific adapters, datasets, models, keys and case details stay in
ignored `local/`. Do not commit them, even to examples or test fixtures.

## ETHAN 跨项目协作

开始任务先读本项目 ETHAN.md，再读取知识库通用规范及相关传递记录。
收尾回传设计、验证与可复用信息，工程实现采用 OpenSpec。
