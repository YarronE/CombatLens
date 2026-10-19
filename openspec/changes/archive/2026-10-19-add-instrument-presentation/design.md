# Design

## Context
The renderer is independent Python/HTML. REA is reached by the agent, not imported by the server. Local adapters prepare research; every run references an adapter ID. Static pages already disallow external image requests.

## Decisions
D1: Shared instrument.css and theme.js apply to both entry points. Use Oxanium (OFL) for Latin display and tabular values, system sans for Chinese. Strict left alignment and grid replace uniform rounded cards. Dark neutral base, parchment text and restrained amber accent are defaults. Explicit game palette overrides are limited to six hex tokens. Cost: full Chinese font remains system-dependent.

D2: Read local/presentations/<adapter-id>/theme.json, with optional presentation.json in a run taking precedence. Resolve assets strictly beneath local/presentations, require PNG/JPEG signature, SHA256 and 12 MiB limit. API returns sanitized values and one fixed image route, never local paths. Invalid data returns generic fallback with a diagnostic. No external URLs used for media. Attribution links allow HTTPS only. This preserves current source hashes and lets future runs inherit the template.

D3: Apply game artwork in a large overview hero and a compact workspace masthead. Keep the model canvas and timeline free of background artwork. Missing imagery uses a deliberate typographic layout. Reduced-motion and focus remain available.

D4: Ship font and OFL notice in vendor; no proprietary typeface or NASA logo. Record source and digest. Do not claim an exact licensed game font or NASA affiliation.

## Verification and rollback
Synthetic tests cover manifest normalization, asset boundaries, digest/type limits and live API defaults. Browser checks cover both real local pages at desktop/narrow widths, image/font load, navigation and model/event actions. Existing model/save tests remain required. Revert this commit to restore earlier layout; no research or analysis schema migration.

## Case boundary
Official artwork, sampled color evidence, screenshots and adapter-specific theme remain ignored. Registered preview models may lack material color data; never describe official image sampling as whole-game package analysis.
