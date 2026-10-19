# Design
## Context and references
Verified: AssetViewer owns one PlaybackClock and reports action/clip time through existing mapping. app.js draws timeline coordinates and stores copy history separately. Shared DOM nodes can be reparented without a second clock.

References: Epic Sequencer Toolbar (https://dev.epicgames.com/documentation/en-us/unreal-engine/sequencer-cinematic-toolbar-in-unreal-engine) for transport, snapping and track tooling. SkillEditorDemo (https://github.com/lsunky/SkillEditorDemo, inspected a4e3e825f75a28c040de3dce6271c70e2411dc62) for typed animation/event configuration through Playables. SuperCLine/actioneditor README was inspected as an action-editor reference; its public Assets tree contains only a logo, so no implementation claim is made. No external code/assets are incorporated.

## Decisions
D1: One .action-editor panel holds AssetViewer, accessible separator and sequencer dock. Existing playback nodes move into the shared transport; asset selectors, clip scrubber/time and evidence move into the right inspector. Keep one renderer/clock. Trade-off: narrow layouts stack details below instead of reproducing a desktop on a phone.
D2: Compact neutral editor panels (#17191c, #24272b, #34383e), existing game accent and bundled display font. Selected intervals use clear borders; point and section events have distinct colors. Preserve theme identity in the compact masthead, without background art behind the working canvas. No imported Unreal branding.
D3: Divider proportion is transient presentation state, bounded to 25–75%; pointer capture cancels on Escape/blur, keyboard arrows adjust. ResizeObserver resizes the existing renderer. No history command or source edit is produced.
D4: Sticky SVG overlay groups for ruler and native track labels compensate horizontal/vertical scrolling in SVG units. All manipulation still uses getScreenCTM. Timeline width is computed from available workspace width and a transient zoom factor; pass that actual width into drag math. Tick spacing uses decimal native coordinates, never assumes FPS. Existing seek gate remains the synchronization authority.
D5: Move event lists and untimed records into a collapsible inspector catalog. Keep forms first in the event inspector, raw source details below. Graph and provenance dialogs remain available. This frees the timeline area without discarding data/actions.

## Validation
Synthetic geometry/tick/split checks plus all existing event, preview and server tests. Real browser must cover desktop simultaneous visibility, playback/seek, resized and zoomed drag, history/save, subject switch, sticky headers, narrow layout and empty synthetic input. Screenshots and real inputs remain local. Roll back this change without migrating any research schema.
