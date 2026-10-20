# Design

Extend clock_mapping unit from seconds to seconds or frames. seconds_per_unit is mandatory for frames and exactly one for seconds when present. Validate dimensions on the server and client. Apply the factor only in actionToClip/clipToAction; retain PlaybackClock sourceRate. Remove hard-coded seconds guards from generic playback controls and labels. Add synthetic tests with an authored frame scale different from registered sampling to prevent accidental FPS inference. Evidence registry checks continue to invalidate changed dependencies.

Browser acceptance exposed overlapping point hit areas in dense native events. Lane packing now accounts for the 24px hit width at the current axis scale, without changing original event coordinates. Frame-status labels carry the proven coordinate unit.
