# Design

Python 3.11+ standard library orchestrates requests and hosts a loopback service.
Native JavaScript and local Three r180 render the existing generic timeline UI.
No cloud account or model API key is required for viewing prepared research.

D1. Local adapter manifest declares aliases, capabilities and a reviewed Python
entrypoint. Registry lives in ignored local/config.json. Explicitly configured
code is trusted; natural language never supplies executable code or paths.
D2. Each run gets a new directory under local/research. Validate package fingerprint,
all source IDs and hashes before replacing the active pointer. On failure retain
prior state and diagnostics; never rewrite original input data.
D3. The source-backed runtime is reused with generic presentation metadata and
predicate-driven rule matching. Game-specific selection/rules stay in local adapters.
D4. Reports separate extraction, import, verification, model availability and
game-runtime validation. Unknown capabilities produce visible gaps.
D5. Case data stays outside public Git. A publish scanner checks the exact staged
file list. Public examples and tests are synthetic and explicitly labelled.
D6. The CLI can start/reuse only a matching loopback service. A foreign port is
left untouched. Analysis copies are isolated under the new project local directory.

Map routing and preparation to CLI/adapter tests; viewing and persistence to
runtime HTTP and frontend tests; publication boundary to staged-file scanning.
Actual assets and browser verification are recorded locally, never as public fixtures.
