# A2A Compliance Plan — Green Agent + Purple Baseline

> **Date:** 2026-04-29  |  **Updated:** 2026-04-29
> **Spec version:** A2A v1.0.0 (GA, March 12 2026)
> **SDK:** `a2a-sdk==1.0.2` (upgraded from 0.3.23)
> **Status:** Phases 1-4 COMPLETE

---

## Executive Summary

**Phases 1-3 are complete.** The codebase has been fully migrated from `a2a-sdk 0.3.23` (Pydantic types, v0.3 wire format) to `a2a-sdk 1.0.2` (protobuf types, v1.0 wire format). This was a larger migration than initially estimated — the SDK v1.0 replaced Pydantic models with Protocol Buffer messages, removed `A2AStarletteApplication` in favor of `Starlette` + route builders, and changed the client API from callback-based to iterator-based.

**Key changes made:**
- All types migrated from Pydantic → protobuf (`a2a.types.a2a_pb2`)
- Server apps use `create_jsonrpc_routes()` + `create_agent_card_routes()` with `enable_v0_3_compat=True`
- Agent Cards use `supported_interfaces` (not legacy `url`), explicit capabilities, correct MIME types
- Client uses `SendMessageRequest` + `AsyncIterator[StreamResponse]` (not callback Consumer)
- `sync_client.py` sends `SendMessage` method, `A2A-Version: 1.0` header, `application/a2a+json` Content-Type
- Error types raised directly (no `ServerError` wrapper)
- Part construction uses `new_text_part()` / `new_data_part()` helpers
- Response parsing handles both protobuf and v0.3 compat formats

---

## 1. SDK Upgrade (CRITICAL — Do First)

| Item | Current | Required | Impact |
|------|---------|----------|--------|
| `a2a-sdk` version | `0.3.23` | `>=1.0.0` (target `1.0.2`) | Unlocks all v1.0 types, bindings, transport options |
| `pyproject.toml` dependency | `a2a-sdk[http-server]>=0.3.5` | `a2a-sdk[http-server]>=1.0.0` | One-line change |

**What the upgrade gives us for free (handled by SDK):**
- PascalCase JSON-RPC method names (`SendMessage` instead of `message/send`)
- Well-known URI routing (`/.well-known/agent-card.json`)
- `A2A-Version` header injection/validation
- Updated Part type models (flattened `oneof` structure)
- Proper A2A error types with spec-defined error codes
- `application/a2a+json` content type

**Files to change:**
- `pyproject.toml:12` — bump version constraint
- `uv.lock` — regenerate after bump

---

## 2. Agent Card Migration (HIGH)

### 2.1 `url` → `supportedInterfaces`

The v1.0.0 spec replaces the flat `url` field with `supportedInterfaces` — an ordered array of `AgentInterface` objects declaring protocol binding and version.

| Field | v0.3 (current) | v1.0.0 (required) |
|-------|----------------|-------------------|
| Endpoint | `url="http://..."` | `supportedInterfaces=[AgentInterface(url="http://...", protocolBinding="jsonrpc", protocolVersion="1.0")]` |

**Files to change:**
- `src/purple_car_bench_agent/server.py:41-50` — `prepare_agent_card()`: replace `url=` with `supportedInterfaces=`
- `src/green_car_bench_agent/server.py:46-55` — `car_bench_evaluator_agent_card()`: same change

### 2.2 Capabilities — explicitly declare what we support

Current: `AgentCapabilities()` (purple) / `AgentCapabilities(streaming=True)` (green)
Required: Explicitly declare all capability flags.

```python
# Purple agent
AgentCapabilities(
    streaming=False,
    pushNotifications=False,
    extendedAgentCard=False,
)

# Green agent
AgentCapabilities(
    streaming=True,
    pushNotifications=False,
    extendedAgentCard=False,
)
```

### 2.3 Input/Output modes — use proper media types

| Agent | Current | Correct |
|-------|---------|---------|
| Purple | `default_input_modes=["text/plain"]` | `["text/plain", "application/json"]` |
| Green | `default_input_modes=["text"]` | `["text/plain", "application/json"]` |

`"text"` is not a valid MIME type. Both agents accept JSON data via DataPart, so `application/json` should also be listed.

---

## 3. Part Type Flattening (HIGH)

The v1.0.0 spec flattens Part types. Instead of separate `TextPart`, `FilePart`, `DataPart` wrapper types, a `Part` now has a `oneof` with fields: `text`, `raw`, `url`, `data`.

**Impact depends on SDK 1.0.x behavior.** If the SDK 1.0.x maintains backward-compatible `TextPart`/`DataPart` aliases (likely, since it has v0.3 compat mode), our existing code may work as-is. If not, every Part construction site needs updating.

**Files that construct Parts (verify after SDK upgrade):**
- `src/purple_car_bench_agent/car_bench_agent.py:256-288` — builds response Parts
- `src/agentbeats/client.py:29,34-43` — `create_message()`, `create_message_with_parts()`
- `src/agentbeats/sync_client.py:12-21` — `create_message_with_parts()`

**Files that parse Parts:**
- `src/agentbeats/client.py:45-52` — `merge_parts()`
- `src/agentbeats/sync_client.py:24-31` — `merge_parts()`
- `src/purple_car_bench_agent/car_bench_agent.py:67-91` — parses incoming Parts

**Action:** Upgrade SDK first, run tests, fix any type breakages.

---

## 4. JSON-RPC Method Names (HIGH)

Our `sync_client.py` manually constructs JSON-RPC requests with v0.3 method names.

| Current (`sync_client.py:46`) | v1.0.0 Required |
|-------------------------------|-----------------|
| `"method": "message/send"` | `"method": "SendMessage"` |

**File to change:**
- `src/agentbeats/sync_client.py:46` — change method name

**Note:** If we refactor `sync_client.py` to use the SDK's client instead of raw HTTP, this is handled automatically. The SDK 1.0.x `ClientFactory` will produce clients that use the correct method names.

---

## 5. Versioning Header (HIGH)

| Requirement | Current | Required |
|-------------|---------|----------|
| Client sends `A2A-Version` header | Not sent | `A2A-Version: 1.0` on every request |
| Server validates `A2A-Version` | Not validated | Must process using requested version semantics |
| Missing header interpretation | N/A | Treat as `0.3` |

**The SDK 1.0.x likely handles this automatically.** Verify after upgrade. If `sync_client.py` stays as raw HTTP, we must add the header manually:

```python
headers={"Content-Type": "application/a2a+json", "A2A-Version": "1.0"}
```

**Files to change:**
- `src/agentbeats/sync_client.py:57-58` — add `A2A-Version` header and update Content-Type

---

## 6. Content-Type (MEDIUM)

| Current | v1.0.0 |
|---------|--------|
| `application/json` | `application/a2a+json` |

The spec registers `application/a2a+json` as the media type for A2A payloads. The SDK should handle this, but `sync_client.py` sets headers manually.

**File to change:**
- `src/agentbeats/sync_client.py:58` — `"Content-Type": "application/a2a+json"`

---

## 7. Purple Agent — Artifacts vs Messages (MEDIUM)

The spec says: *"Messages SHOULD NOT deliver task outputs. Results SHOULD use Artifacts."*

Currently, the purple agent returns results as a `Message` with Parts (via `new_agent_parts_message()`). It should instead emit an `Artifact` for the actual task output (tool calls, final answer) and use Messages only for conversational turns.

**However:** For our multi-turn tool-calling pattern (green sends prompt → purple returns tool calls → green executes → sends results → repeat), using Messages for intermediate turns is appropriate. Only the **final response** (no more tool calls) should be an Artifact.

**File to change:**
- `src/purple_car_bench_agent/car_bench_agent.py:327-331` — when the response has no tool calls (final answer), emit an Artifact instead of a Message

---

## 8. Task Lifecycle — Missing States (MEDIUM)

| State | Implemented | Should Implement |
|-------|-------------|-----------------|
| `submitted` | Yes (via SDK) | Yes |
| `working` | Yes | Yes |
| `completed` | Yes | Yes |
| `failed` | Yes | Yes |
| `canceled` | Raises `UnsupportedOperationError` | Implement properly |
| `input-required` | Not used | Nice-to-have |
| `auth-required` | Not used | Not needed (local/docker) |
| `rejected` | Not used | Nice-to-have |

**Priority: Implement `CancelTask`** for the green agent (long-running evaluations):
- `src/agentbeats/green_executor.py:74-77` — implement actual cancellation instead of raising error
- Need a cancellation flag in `CARBenchEvaluator` that `run_eval()` checks periodically

---

## 9. Error Handling (MEDIUM)

The v1.0.0 spec defines 9 specific error types with standardized codes:

| Error | Code | We Use? |
|-------|------|---------|
| `JSONParseError` | -32700 | SDK handles |
| `InvalidRequestError` | -32600 | SDK handles |
| `MethodNotFoundError` | -32601 | SDK handles |
| `InvalidParamsError` | -32602 | Yes (`green_executor.py:49,51`) |
| `InternalError` | -32603 | Yes (`green_executor.py:72`) |
| `TaskNotFoundError` | -32001 | SDK handles |
| `TaskNotCancelableError` | -32002 | No — we raise `UnsupportedOperationError` |
| `UnsupportedOperationError` | -32003 | Yes (`green_executor.py:77`) |
| `ContentTypeNotSupportedError` | -32004 | No |
| `PushNotificationNotSupportedError` | -32005 | No |

**Action:** After implementing `CancelTask`, use `TaskNotCancelableError` for tasks that are already terminal. Current coverage is acceptable for our use case.

---

## 10. Well-Known URI for Agent Card (MEDIUM)

| Current | v1.0.0 |
|---------|--------|
| SDK serves card at agent root URL | Must be at `/.well-known/agent-card.json` |

**The SDK 1.0.x should handle this.** Verify after upgrade that `A2AStarletteApplication` serves the card at the well-known path.

**Files to verify:**
- `src/purple_car_bench_agent/server.py:105-108`
- `src/green_car_bench_agent/server.py:97-100`

**Client-side:** `A2ACardResolver` in the SDK should already look at the well-known URI.
- `src/agentbeats/client.py:57-58` — verify `A2ACardResolver` behavior after upgrade

---

## 11. Security (LOW for local/Docker, HIGH for production)

| Feature | Current | v1.0.0 Requirement |
|---------|---------|-------------------|
| Transport | HTTP | HTTPS with TLS 1.2+ in production |
| Auth | None | `securitySchemes` in Agent Card |
| Per-request auth | None | Credentials in every request |
| Data scoping | None | Per-authenticated-client data access |

**Not needed for local/Docker evaluation.** Required before any production deployment.

**Files to change (when ready):**
- Both `server.py` files — add `securitySchemes` and `securityRequirements` to Agent Cards
- Client code — add auth credential injection

---

## 12. Features NOT Needed (Confirmed Low Priority)

| Feature | Why Not Needed |
|---------|---------------|
| Server-side incremental streaming | Tasks complete quickly; full responses are sufficient for our turn-based pattern |
| Push Notifications | Tasks complete within HTTP timeout; streaming covers our needs |
| Extended Agent Card | No auth tiers; all capabilities are public |
| `SubscribeToTask` | We use streaming on send, not subscription to existing tasks |
| `ListTasks` | Single-task evaluation pattern |
| FilePart / `raw` / `url` Parts | We exchange text and structured JSON only |
| Extensions | No custom extensions needed |
| Agent Card Signing (JWS) | Local/Docker deployment; no integrity verification needed |
| Multi-tenancy | Single-tenant evaluation setup |
| gRPC binding | JSON-RPC is sufficient |
| HTTP+JSON/REST binding | JSON-RPC is sufficient |
| `messageId` idempotency/dedup | Single-client evaluation; no duplicate request risk. Servers MAY implement per spec |
| `referenceTaskIds` cross-linking | Linear eval conversations use `contextId` only; no cross-task references needed |

---

## 13. Implementation Order (Prioritized)

### Phase 1 — SDK Upgrade & Wire Format ✅ COMPLETE
1. ~~Bump `a2a-sdk` to `>=1.0.0` in `pyproject.toml`~~ → Done (v1.0.2)
2. ~~Regenerate lock file (`uv lock`)~~ → Done
3. ~~Fix type/import breakages~~ → Full migration from Pydantic to protobuf types
4. ~~Verify Part types work~~ → Using `new_text_part()` / `new_data_part()` helpers
5. ~~Verify well-known URI routing~~ → `create_agent_card_routes()` serves at `/.well-known/agent-card.json`

### Phase 2 — Agent Card v1.0.0 ✅ COMPLETE
6. ~~Migrate `url` → `supportedInterfaces`~~ → Both agents use `AgentInterface(url, protocol_binding, protocol_version)`
7. ~~Explicitly declare all capabilities~~ → `streaming`, `push_notifications`, `extended_agent_card` all set
8. ~~Fix MIME types~~ → `["text/plain", "application/json"]`

### Phase 3 — Client Compliance ✅ COMPLETE
9. ~~Update `sync_client.py`~~ → `SendMessage` method, `application/a2a+json`, `A2A-Version: 1.0`
10. ~~Update `client.py`~~ → Uses SDK `Client.send_message(SendMessageRequest)` with `AsyncIterator[StreamResponse]`
11. ~~Update `client_cli.py`~~ → Migrated from Consumer callback to direct `StreamResponse` iteration

### Phase 4 — Server Compliance ✅ COMPLETE
12. ~~Purple agent: emit Artifacts for final responses~~ → Final answers (no tool calls) emitted as Artifact on completed Task; intermediate turns remain Messages
13. ~~Green agent: implement CancelTask~~ → Tracks active tasks with `asyncio.Event`, signals cancellation, emits `canceled` status. Raises `TaskNotCancelableError` for unknown tasks

### Phase 5 — Production Readiness (when needed)
14. HTTPS + TLS
15. Security schemes in Agent Cards
16. Auth credential injection in clients

---

## 14. Files Changed (Summary)

| File | Changes |
|------|---------|
| `pyproject.toml` | ✅ Bumped `a2a-sdk>=1.0.0` |
| `src/purple_car_bench_agent/server.py` | ✅ Protobuf AgentCard with `supportedInterfaces`, `Starlette` + route builders, explicit capabilities, correct MIME types |
| `src/green_car_bench_agent/server.py` | ✅ Same as purple server |
| `src/purple_car_bench_agent/car_bench_agent.py` | ✅ Protobuf Part parsing (`WhichOneof`), `new_text_part()`/`new_data_part()` construction, **Artifacts for final responses** (Messages for intermediate tool-call turns) |
| `src/green_car_bench_agent/car_bench_evaluator.py` | ✅ Protobuf Part construction, `MessageToDict` for data parsing, `TaskState.TASK_STATE_*` enums, `new_text_message()`, dual-format response parsing (Message + Artifact) |
| `src/agentbeats/green_executor.py` | ✅ Direct error raising (no `ServerError`), `new_task_from_user_message()`, `TaskState.TASK_STATE_*`, **CancelTask support** with active task tracking |
| `src/agentbeats/sync_client.py` | ✅ `SendMessage` method, `A2A-Version: 1.0`, `application/a2a+json`, protobuf `MessageToDict` serialization |
| `src/agentbeats/client.py` | ✅ SDK `Client.send_message(SendMessageRequest)`, `AsyncIterator[StreamResponse]`, protobuf types throughout |
| `src/agentbeats/client_cli.py` | ✅ Direct `StreamResponse` iteration (replaced Consumer callback), protobuf Part parsing |

---

## 15. Compliance Estimate After All Phases

```
Phase 1+2+3+4 (DONE): ██████████████████░░  ~90% compliant (wire-format + server correctness)
Phase 5:              ████████████████████  ~100% compliant (production-ready)
```

**Phases 1-4 are complete.** The codebase is A2A v1.0.0 compliant at the wire-format AND server-behavior level. Phase 5 (HTTPS, auth) is only needed for production deployment.
