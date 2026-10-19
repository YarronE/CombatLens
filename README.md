# CombatLens

面向动作游戏玩家和专业战斗策划的本地研究工具。让 Agent 接收一句研究请求，
通过已登记适配器准备来源数据，生成分析概览与可编辑的动作工作区。

```sh
python run.py demo --open
python run.py doctor
python run.py register /path/to/reviewed-adapter.json
python run.py analyze "分析我已登记的游戏，生成战斗工作台" --open
```

Python 3.11+，查看与合成演示无需 pip 安装。打开 `--open` 返回的本地URL。
该参数启动服务，不自动操控浏览器。未登记的游戏会报告适配缺口。
新 clone 只有合成演示，不包含任何真实游戏案例、适配器、模型或解包结果。

## Agent 一句话入口

使用 `skills/combatlens/SKILL.md`，在目标 Agent 的技能安装方式中登记该目录。
Skill 使用同一 CLI，并依据适配器能力选择 REA 调查或本地解析。
REA 提供程序与证据调查；游戏格式支持由适配器声明。工具不会把导入旧研究包
标记为本轮解包，不承诺任意游戏自动完整还原。

## 可查看的内容

- 当前角色或Boss的技能、原始事件、Timeline与来源。
- 已登记的模型、骨骼动画和有依据的时间同步。
- 3C、数值、资源与AI的已恢复规则，以及明确的未知范围。
- 独立分析副本、参数修改、来源保护、冲突检测和保存重开。

## 本地适配器

适配器是经过操作者审查的 Python 文件，提供 `prepare(request, output_dir)`，
返回运行报告并生成研究包、Timeline和来源登记。配置位于忽略的 `local/`。
接口见 [适配契约](docs/ADAPTERS.md)，不从自然语言执行脚本或自动下载适配器。

公开仓库只收录通用工具和自有合成测试。真实案例留本机；源码采用MIT，
Three保留其原许可证。见 [第三方说明](THIRD_PARTY_NOTICES.md)。

## 验证

```sh
python -m unittest discover -s tests -v
node --test web/model.test.mjs web/preview-model.test.mjs web/selection-model.test.mjs
python scripts/check_publish.py
```

运行状态与实际边界见 [STATUS](docs/STATUS.md)。
