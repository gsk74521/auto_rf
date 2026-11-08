# platynui-windows-runtime Specification

## Purpose
TBD - created by archiving change fix-platynui-windows-runtime. Update Purpose after archive.
## Requirements
### Requirement: Desktop automation never leaves keyboard modifiers held
The system SHALL track every synthetic keyboard key it presses in a held-key registry and SHALL
release the **exact set of keys still held** — including non-modifier keys (letters, digits,
function keys, `Escape`, `Enter`, arrows, `Space`, `Tab`, etc.), not only modifiers (Ctrl, Alt,
AltGr, Shift, Win) — whenever a PlatynUI desktop session ends, a keyboard keyword fails or times
out, or the server process exits, so that an interrupted or killed run can never leave the user's
keyboard physically wedged.

A synthetic key-DOWN dispatched via `Keyboard Press` (and the transient down inside `Keyboard Type`
and chord expansion) SHALL be recorded in the registry, and the matching key-UP (via
`Keyboard Release`, or the up inside `Keyboard Type`) SHALL remove it, so the registry reflects only
keys currently held by rf-mcp.

The release SHALL be best-effort and non-raising, SHALL be a no-op when the registry is empty (no
key is held), and SHALL NOT start the native runtime solely to perform a release (it acts only when
the runtime is already open). A deliberate `Keyboard Press` that is still held when the session ends
SHALL be released by this path AND SHALL surface a warning steering agents toward the atomic
`Keyboard Type <chord>` over a bare `Keyboard Press`, which sends key-down only and must be paired
with `Keyboard Release`. A steering-confidence downgrade (the native keyword actually succeeded and
holds the key intentionally) SHALL NOT trigger a premature release.

#### Scenario: Session end releases held modifiers
- **WHEN** a PlatynUI desktop session is closed after a run that left one or more keys held
  (including a non-modifier such as `A`, `F12`, or `Escape` pressed via a bare `Keyboard Press`)
- **THEN** the plugin's session-end teardown dispatches a key-UP for exactly the keys recorded in
  the held-key registry, clears the registry, and is a no-op when nothing is held

#### Scenario: Keyword failure or timeout releases held modifiers
- **WHEN** a desktop keyboard keyword (`Keyboard Press`/`Keyboard Type`/`Keyboard Release`) raises
  or times out mid-execution while a key-DOWN is recorded as held
- **THEN** a `finally`/except path releases the tracked held keys before the error is returned, so a
  key or chord killed mid-flight does not leave a key down

#### Scenario: Process exit releases held modifiers
- **WHEN** the server process receives SIGTERM or exits gracefully after desktop use has begun with
  keys still recorded as held
- **THEN** an atexit/signal handler registered once on first desktop use releases exactly the
  tracked held keys

#### Scenario: Deliberate Press/Release chord is preserved
- **WHEN** an agent issues `Keyboard Press <Shift>` intending to release it later with
  `Keyboard Release <Shift>` within the same active session
- **THEN** the successful press records the key as held and NO premature release is dispatched, so
  the later `Keyboard Release` behaves correctly and clears the registry entry

#### Scenario: Steering downgrade does not release
- **WHEN** a desktop keyboard keyword's success is flipped to failure by the steering-confidence
  gate (the native keyword actually executed and holds its key as intended)
- **THEN** the failure-path release is NOT dispatched, so a deliberate held key is not corrupted

#### Scenario: Release never resurrects the runtime
- **WHEN** the release path runs but the native runtime is not open
- **THEN** it returns without starting the runtime and without raising

### Requirement: Desktop keyword queries fail fast and honor timeout_ms
The system SHALL bound PlatynUI desktop keyword queries with a short default timeout (rather than
PlatynUI's ~30s / ~60s library default) and SHALL honor a caller-supplied `timeout_ms` by mapping
it onto the PlatynUI query override, so that a wrong or honest-miss locator fails in ~1–2 seconds
and cannot stack into multi-minute stalls.

The short default SHALL remain overridable per session so a deliberately long wait (e.g. for an
application window to appear) can request a larger `timeout_ms`.

#### Scenario: Honest-miss locator fails fast
- **WHEN** a desktop keyword targets a locator that does not resolve
- **THEN** the query fails within the short default (~1.5s) instead of waiting PlatynUI's ~30s/60s
  default

#### Scenario: Caller timeout is honored
- **WHEN** a desktop keyword is executed with an explicit `timeout_ms`
- **THEN** that value is mapped onto the PlatynUI query override for the call and governs the wait

### Requirement: Desktop keyword execution never blocks the server event loop
The system SHALL execute PlatynUI desktop/native keywords off the server event loop (via a worker
thread) with a bounded wait, so that a slow desktop query cannot wedge the server or starve
unrelated calls such as metadata lookups.

#### Scenario: Metadata calls stay responsive during a slow desktop query
- **WHEN** a desktop `Focus`/`Query` on a large tree is in progress
- **THEN** the event loop remains free and concurrent metadata calls (e.g. `get_keyword_info`)
  return promptly instead of hanging behind the query

#### Scenario: Slow desktop call returns a bounded failure
- **WHEN** an off-thread desktop keyword exceeds its bounded wait
- **THEN** the caller receives a timeout failure without the loop having been blocked

### Requirement: The desktop safety guard is platform-aware on Windows
The system SHALL classify a Windows host as a distinct `windows` desktop state and, by default,
SHALL allow PlatynUI interaction keywords on Windows with a one-time active-desktop warning and a
Windows-accurate note, rather than refusing every keyword with a Linux-only Xephyr/Xvfb remediation
that cannot be followed on Windows.

The Windows branch SHALL leave the Linux isolated/active/unknown classification and its
refuse-by-default behaviour unchanged, and SHALL keep a strict opt-in for operators who want
isolation enforced on Windows.

#### Scenario: Windows host is allowed by default
- **WHEN** a PlatynUI interaction keyword runs on a Windows host with no explicit override
- **THEN** the guard classifies the display as `windows`, allows the keyword (not bypassed), and
  emits a one-time warning that it will drive the active desktop

#### Scenario: No Linux remediation is shown on Windows
- **WHEN** the safety guard evaluates a Windows host
- **THEN** the returned reason/remediation contains no Xephyr/Xvfb recipe and instead references a
  dedicated/RDP session for isolation

#### Scenario: Linux behaviour is unchanged
- **WHEN** the guard evaluates a Linux host with an active EWMH desktop and no isolation marker
- **THEN** it still refuses by default exactly as before

### Requirement: Held keys are recovered after a hard process termination
The system SHALL persist the held-key registry to a durable per-runtime state file at the moment a
key-DOWN is recorded (and update/clear it on release), so that a **hard termination** of the server
process — SIGKILL, `TerminateProcess`, `Stop-Process -Force`, or a crash — that runs neither the
`atexit` nor the `SIGTERM` handler cannot permanently leave a key held. On the next desktop
`on_session_start` the successor process SHALL read the state file, dispatch a key-UP for every key
it records, and then clear the file.

Recovery SHALL be best-effort and non-raising: dispatching a key-UP for a key that is not actually
held is a harmless no-op, so a stale state file is safe to replay. The state file SHALL be scoped so
that it cannot cause a healthy concurrent runtime to release a key another live session is
deliberately holding (e.g. keyed by process/runtime identity and only replayed for records the
current process did not itself write).

#### Scenario: Force-killed run's stuck key is released on next start
- **WHEN** a prior server process was force-killed (`TerminateProcess`/SIGKILL) while a key it
  pressed was still held, leaving a persisted held-key state file
- **THEN** the next PlatynUI desktop `on_session_start` reads the file, dispatches key-UPs for the
  recorded keys, and clears the file — clearing the wedged key without operator intervention

#### Scenario: Clean shutdown leaves no stale state
- **WHEN** a desktop session releases its held keys through the normal teardown/exit path
- **THEN** the persisted state file is cleared, so a later start performs no unnecessary replay

#### Scenario: Stale replay is a safe no-op
- **WHEN** the recovery path replays a state file whose recorded keys are no longer physically held
- **THEN** the dispatched key-UPs are harmless no-ops and no error is raised

