# Installation and REA

CombatLens is an independent renderer, CLI and agent workflow. It is not a fork,
modified distribution or bundled installation of REA.

| Task | Required |
| --- | --- |
| View prepared local research / synthetic demo | CombatLens and Python 3.11+; browser |
| One-sentence research request | Above plus a compatible agent, CombatLens Skill, reviewed adapter and local game inputs |
| Investigate programs using REA | Agent connected to a separate REA MCP; required analysis providers depend on the target |
| Unpack a game container | Format reader, codec and locally supplied inputs required by its adapter; REA alone does not guarantee format support |

If an agent already exposes REA tools, reuse that connection. A missing `rea`
command in PATH does not establish that MCP is unavailable. CombatLens does not
automatically install REA or analysis engines and does not change client configs.

For a new REA connection follow the current official instructions:
[REA installation](https://github.com/morluto/rea/blob/main/docs/installation.md).
The documented setup entry point checked on 2026-10-19 is `npx rea-agents setup`;
review its client/configuration plan. Package setup is separate from installing
CombatLens. A future guided installer can simplify this without claiming REA is
already bundled in the current release.

For CombatLens clone the repository, then run:

```sh
python run.py doctor
python run.py demo --open
```

Open the reported loopback URL. Register the bundled Skill with your agent for
natural-language requests. Register reviewed adapters and supply game files locally.
A fresh clone contains no game case. Viewing is offline; fonts are bundled. Game
artwork and palette are optional private inputs, described in ADAPTERS.md.
