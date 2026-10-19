# Presentation

## Requirements
### Requirement: Shared visual workspace
Both pages MUST use aligned grid layouts, bundled display typography, visible focus and usable narrow layouts. Game identity MUST be supplied through data.
#### Scenario: Prepared research
Opening a prepared run displays its title, counts and navigation; the action workspace retains selection, model and event functions.
#### Scenario: Narrow screen
At 390px both pages fit the document width and controls remain usable.

### Requirement: Private visual inputs
The renderer MUST serve only an explicitly registered, digest-checked PNG or JPEG beneath local/presentations. Missing, stale or invalid input MUST preserve generic navigation and show a diagnostic. It MUST NOT expose arbitrary files or make remote image requests.
#### Scenario: Reviewed artwork
Both pages display the registered image and credit. A later generated run using the same adapter inherits the visual identity.
#### Scenario: Unsafe input
Traversal, symlink escape, invalid colors, unsupported image bytes or digest mismatch do not produce an asset response.
#### Scenario: No presentation
Fresh synthetic demo uses the shared layout without game assets or a broken image.

### Requirement: Accurate prerequisites
README MUST distinguish viewing/importing from new program investigation and state that REA is separately connected, not bundled or forked.
#### Scenario: New user
The installation guide identifies Python for viewing, an agent and format readers for extraction, and REA for REA-backed investigation. No REA reinstall is required when the agent already has it.
