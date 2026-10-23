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

## 是否需要 REA

查看已有研究和合成演示只需本工具、Python 与浏览器。使用 Agent 调用 REA
调查新游戏程序时，另行连接 REA MCP；已有连接可直接复用。CombatLens 是
独立工具，通过 Agent 配合 REA，未内置或修改分发 REA。解包还需要适配器对应的
格式读取器与本地输入。安装分工见 [安装说明](docs/INSTALLATION.md)。

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

## Timeline 直接编辑

进入动作工作区并切换到“分析副本”。拖动事件本体可整体移动，拖动区间两端
可调整开始或结束。原始事件保持只读。重叠事件自动分行，原始轨道字段不变。
时间吸附可选择细步长、粗步长或不吸附；方向键微调，Shift 增大步长。

使用“撤销 / 重做”、Ctrl/Cmd+Z、Ctrl/Cmd+Shift+Z 或 Ctrl+Y 回放操作。
输入框保留原生撤销。一次拖拽对应一步；表单、新增、隐藏和恢复也进入历史。
Esc、失焦或丢失指针捕获会取消当前拖拽。历史保留当前会话最近100步，
切换或重新打开另一副本时清空。保存后的时间和参数可以重开，服务端修订号不回退。

模型按已有证据对应时间预览，超出已登记动画片段或单位不对应时会提示缺口。
更改仅属于分析假设，不写回游戏。查看 [编辑说明](docs/EDITING.md)。

## 播放区间与逐帧查看

拖动标尺上方的两端标记选择播放区间，也可在“区间”中填写数值后应用。
关闭“循环”时在终点停止，开启后反复播放所选区间。切换动画会重置选择。

标尺可切换“秒 / 帧”，用 ‹ / › 查看上一帧、下一帧。帧号来自登记动画采样
序列，不假定实机FPS；2×等原始倍率仍按证据换算。播放选区只影响当前预览，
不会进入事件修改或保存数据。低频视图工具、文件操作与来源说明按需展开。

## 事件详情与动画定位

点击事件，查看已核验的作用、触发条件和关联数值，并暂停到对应动画采样帧。
定位使用映射起点之后的首个登记采样；帧号不代表游戏运行时回调发生帧。
缺少执行证据、实例条件不符或来源变化时显示“未确认”，不根据 Notify 名称猜测。
数值保留原单位和适用范围，原始字段与技术依据按需展开。分析副本中的解释明确
标为原始实例证据，不把修改参数当成执行结果。本地解释格式见适配契约。

## 本地适配器

适配器是经过操作者审查的 Python 文件，提供 `prepare(request, output_dir)`，
返回运行报告并生成研究包、Timeline和来源登记。配置位于忽略的 `local/`。
接口见 [适配契约](docs/ADAPTERS.md)，不从自然语言执行脚本或自动下载适配器。

公开仓库只收录通用工具和自有合成测试。真实案例留本机；源码采用MIT，
Three保留其原许可证。见 [第三方说明](THIRD_PARTY_NOTICES.md)。

## 验证

```sh
python -m unittest discover -s tests -v
node --test web/model.test.mjs web/preview-model.test.mjs web/selection-model.test.mjs web/execution-model.test.mjs web/timeline-edit.test.mjs web/editor-layout.test.mjs web/playback-range.test.mjs web/designer-model.test.mjs
python scripts/check_publish.py
```

运行状态与实际边界见 [STATUS](docs/STATUS.md)。

## 保存到本地游戏分析包

```sh
python run.py freeze /path/to/game-project/local/snapshots/version --research /path/to/run
```

目标目录必须尚不存在。归包包含固定页面与运行代码、研究数据、已登记证据和
预览文件，以及匹配当前研究的已保存副本。解释与主题也会固定，原始包字节和
研究指纹保持不变。用 `--attachment FILE` 附带选定验收文件，每份最多16 MiB。

在包目录运行 `python run.py start`，打开返回的本地URL。归包数据只留本地，
不要提交整个目录。包会复制已登记证据，可能占用较多空间，结果回执列出字节数。
当前采用固定本机路径，移动目录后需要重新绑定来源；完整跨设备恢复尚未验证。

静态模型无需先有骨骼动画。适配器可明确登记 static_mesh，工作台显示真实几何，
并禁用缺少依据的播放与逐帧。原生配置状态不自动当成独立招式，未确认的时钟
继续使用来源坐标。副本列表只显示当前Build和研究指纹，其他案例文件保留原位。

## 多对象研究目录

同一项目可登记多个独立研究包，通过页面顶部的选择框切换。每个对象只加载自己的来源、Timeline与AI，分析副本按研究包指纹隔离。已有单研究包链接保持可用。目录格式见 [适配器说明](docs/ADAPTERS.md#workspace-collection)。


## Evidence design study

The action inspector provides three views for event rhythm, ranges/numbers,
and phase/selection conditions. Local adapters may attach reviewed evidence via
`design-study.json`; see [the contract](docs/ADAPTERS.md#optional-evidence-design-study).
Facts retain field provenance. Unknown conditions remain gaps. Confirmed event
coordinates seek only through a proven matching preview clock and registered
samples. Analysis copies preserve the original study as a read-only reference.
