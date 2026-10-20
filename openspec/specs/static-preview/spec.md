# Static preview evidence
- A ready preview can explicitly declare kind=static_mesh, with no clips/skin or
  animation. The default remains skinned_animation with existing strict checks.
- Validate actual finite geometry, indices, hierarchy, embedded GLB bounds and
  exact hash/length. Static mode rejects hidden skin/animation declarations.
- Display true static geometry and allow observation/rotation/reset. Disable
  playback, frames, bone/follow controls and clock mapping. State the missing
  skeletal binding in one concise line, with raw asset proof folded.
- Changing object/asset clears prior geometry and clocks, including async loads.
- Native event coordinates remain native source units when execution clock and
  endpoint precedence are unknown. Never interpret frame fields as sampled FPS.
- A shared renderer serves both modes; no case ID or dataset enters public code.
