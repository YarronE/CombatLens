# Agent workspace

## ADDED Requirements

### Requirement: Explicit request routing
The tool SHALL route a user's request to one registered local adapter, or return
an unsupported/ambiguous diagnostic. Prompt text MUST NOT become shell commands.
#### Scenario: Known local adapter
WHEN a request names a configured alias THEN create a new research run, report
the operation actually performed and publish the workspace only after validation.
#### Scenario: Unsupported request
WHEN no adapter matches THEN preserve current output and report the missing adapter.

### Requirement: Source-backed preparation
Adapters SHALL return compatible research, timeline and source registration data.
The tool MUST preserve native evidence and distinguish extraction from import.
#### Scenario: Changed source
WHEN a registered source digest differs THEN fail preparation without switching
the active workspace or altering an earlier run.

### Requirement: Research and editing
The workspace SHALL expose objects, original events, supported animation previews,
evidence details and separate analysis copies. Unknown time stays unknown.
#### Scenario: Local preview
WHEN a registered rig and clip match current source identity THEN show the actual
model; otherwise retain timeline access with the concrete preview limitation.
#### Scenario: Persistence
WHEN analysis edits are saved THEN confirm a new revision after atomic write.
Conflicting revisions MUST preserve the user's input and original evidence.

### Requirement: Public distribution boundary
Public Git SHALL contain only generic code, contracts and synthetic test material.
#### Scenario: Release scan
WHEN preparing a commit THEN reject local case data, proprietary asset extensions,
credentials and game-specific code or labels outside the ignored local directory.

### Requirement: Agent handoff
The Skill SHALL use the same CLI, report coverage and open the resulting workspace.
#### Scenario: One sentence
WHEN a user requests a supported game study THEN reuse registered local paths,
run preparation and report URL, files and unresolved evidence without asking for
already configured values or claiming unsupported extraction completed.
