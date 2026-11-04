---
title: Branch on the error code, never on the status or the message
impact: CRITICAL
impactDescription: Several codes share one HTTP status and need opposite handling; retrying the wrong one double-sends or hammers a restricted number
tags: errors, codes, 429, retry, Retry-After, 502, 504
---

## Branch on the error code, never on the status or the message

Every error is JSON with a stable `code` and a human `error` message:

```json
{ "code": "unauthorized", "error": "..." }
```

- Branch on `code`. The `error` text can change; show it, never parse it.
- Treat an unknown code as a generic failure, not as success and not as
  "retry forever".
- On a connection-level failure the body also has `reason`: one of
  `proxy_unreachable`, `proxy_auth_failed`, `proxy_tls_failed`, `proxy_timeout`,
  `proxy_dns_failed` or `connect_failed`.

### Every code

<!-- BEGIN GENERATED: errors-table (do not edit; run node tools/generate.mjs) -->

| Code | HTTP | Meaning | Do |
|---|---|---|---|
| `invalid_body` | 400 | The body is not valid JSON, or has a field this route does not take. | fix |
| `invalid_request` | 400 | The request could not be completed as sent. Also the code for an error with no more specific one. | fix |
| `up_to_range_too_large` | 400 | Legacy, no longer returned. Older gateways sent it when a read with `up_to` covered too many messages or senders. A current gateway receipts the oldest part and answers 200 with `partial: true`; repeat the same request until `partial` is absent. | fix |
| `field_not_allowed` | 400 | The body has a key this route does not accept (for example an extra key on a webhook receiver). | fix |
| `header_not_allowed` | 400 | The request carried an account header that the public API refuses. Send only the bearer token. | fix |
| `quote_not_found` | 400 | The `quoted` message is not in this channel's log. | fix |
| `quote_wrong_chat` | 400 | The `quoted` message belongs to another chat. | fix |
| `media_fetch_failed` | 400 | The gateway could not fetch the media URL: it did not answer, answered with an error, or is not a public internet address. | fix |
| `media_type_unsupported` | 400 | The file is not a type this kind of message can carry. The type is read from the file itself. | fix |
| `media_too_large` | 400 | The media is larger than its kind allows: 5 MiB for an `image`, 16 MiB for `video`, `audio` and `voice`, 32 MiB for a `document`. | fix |
| `unauthorized` | 401 | The token is missing, too short or not valid, or the channel ID does not exist. | auth |
| `credential_stale` | 401 | The token stopped applying mid-request: it was replaced, or the channel was removed. | auth |
| `slot_ended` | 401 | This channel's paid slot has ended. The owner renews it in the console. | human |
| `admin_only_field` | 403 | The webhook list drops a receiver whose media setting was set in the console. Keep that receiver, or remove it in the console. | human |
| `account_forbidden` | 403 | This account may not access that resource. | human |
| `account_suspended` | 403 | The account that owns this channel is on hold. Contact support. | human |
| `number_forbidden` | 403 | A number in `mentions` cannot be used. | fix |
| `blocked` | 403 | This channel is blocked: the safety guard unlinked a number it may not use. Fix the pairing in the console. | human |
| `media_forbidden` | 403 | One answer for media that belongs to another channel, to nobody, or does not exist. | fix |
| `not_found` | 404 | The route does not exist, or `webhooks/test` named a url this channel has not configured. An unknown channel answers 401, not 404. | fix |
| `message_not_found` | 404 | That message is not in this channel's message log. | fix |
| `not_own_message` | 403 | This channel did not send that message. A channel can delete only its own messages for everyone. | fix |
| `revoke_window_passed` | 409 | The message is more than 48 hours old, too old to delete for everyone. | fix |
| `revoke_in_progress` | 409 | A delete of that message is already in progress. Try again once it has returned. | wait |
| `not_linked` | 409 | The channel has no linked phone. Link it in the console. | human |
| `stood_down` | 409 | The gateway paused this number after WhatsApp pushed back on it. Reconnect it in the console once the restriction ends. | human |
| `verification_failed` | 409 | The subgroup WAS created, and checking it afterwards definitively failed. `group_jid` names it. Do not create it again. | inspect |
| `rate_limited` | 429 | A gateway flood guard refused a burst, or a webhook test came before its cooldown. `window` names what refused you. | wait |
| `whatsapp_rate_limited` | 429 | WhatsApp itself throttled the number, not a ceiling of the gateway. No Retry-After: WhatsApp does not say how long. | backoff |
| `whatsapp_disconnected` | 503 | The WhatsApp connection dropped before the request completed; the response cannot tell whether the write was sent; treat any write as possibly applied; list or read the state of what you changed before retrying a write; never re-create (e.g. a group) without reading/listing first; reads can be retried after a short back-off | inspect |
| `whatsapp_timeout` | 503 | WhatsApp did not answer an info query in time; the response cannot tell whether the write was sent; treat any write as possibly applied; list or read the state of what you changed before retrying a write; never re-create (e.g. a group) without reading/listing first; reads can be retried after a short back-off | inspect |
| `daily_send_cap_exceeded` | 429 | An operator stop: sends on this channel are stopped (a ceiling of 0, or the operator's own warming programme). Not a usage limit; it may not clear at `resets_at`. | human |
| `checks_spaced_out` | 429 | Checks are spaced out. Retry after retry_after seconds. | wait |
| `check_allowance_used` | 429 | The channel's daily or hourly check allowance is used. Retry at resets_at. | wait |
| `daily_cap_group_add` | 429 | Warm-up protection is on and today's group-add allowance is used. | wait |
| `daily_cap_contact_write` | 429 | Warm-up protection is on and today's contact-save allowance is used. | wait |
| `daily_cap_contact_check` | 429 | Warm-up protection is on and today's number-check allowance is used. | wait |
| `sandbox_allowance_exceeded` | 429 | The sandbox channel used up one of its allowances. `window` says which; it clears at `resets_at`. Paid channels never get it. | wait |
| `gateway_busy` | 429 | The gateway is still working on this channel's earlier requests. Nothing was queued. | wait |
| `channel_unentitled` | 403 | This channel has no paid slot and is not the account's sandbox channel, so it may not send. | human |
| `internal_error` | 500 | The gateway could not complete the request. | retry |
| `upstream_unreachable` | 502 | The service behind the edge could not be reached, or did not answer in time. | retry |
| `upstream_redirect` | 502 | The service behind the edge answered with a redirect. | retry |
| `upstream_not_json` | 502 | The service behind the edge answered with something unreadable. | retry |
| `upstream_not_relayable` | 502 | The answer could not be passed back safely. | retry |
| `upstream_too_large` | 502 | The media object is larger than the public API relays. | fix |
| `upstream_unavailable` | 503 | The token could not be checked right now. | retry |
| `media_upload_failed` | 502 | The upload to WhatsApp failed and nothing was sent, so it is safe to try again. | retry |
| `operator_unresolved` | 503 | The gateway could not confirm its own account setup for a moment. Nothing about the channel is wrong. | wait |
| `read_unresolvable` | 503 | A read receipt could not find the other side's address. | retry |
| `history_unresolvable` | 503 | A history read was refused rather than answered short, because the peer's other address could not be resolved. | retry |
| `audit_unavailable` | 503 | The read could not be recorded first, so it was not served. Try again. | retry |
| `history_sync_off` | 409 | Synced history is turned off for this channel, so older messages cannot be requested. | human |
| `no_history_anchor` | 404 | The channel has no message in that chat to ask for older history from. | fix |
| `history_request_too_soon` | 429 | A history request for this channel or chat was made too recently. Wait `retry_after` seconds. | wait |
| `history_unavailable` | 503 | Synced history is unavailable on this gateway right now. | retry |
| `send_unconfirmed` | 504 | The outcome of a send is UNKNOWN: it may have reached WhatsApp. The body has `ambiguous: true` and the `id` of the logged send. | unknown |
| `receipt_partial` | 502 | Some read receipts went out before the read failed. `receipted` says how many. Resending the same request could receipt them twice. | partial |
| `lane_reclaimed` | 503 | A call made under a phone lane reached the lane's deadline. The body always has `ambiguous`. If ambiguous is false, nothing was done. If ambiguous is true, the add may have gone through; check membership before retrying. | wait_ambiguous |
| `lid_lookup_not_granted` | 403 | The LID lookup routes (`/lids/pn/{phone}`, `/lids/{lid}`) are not available to customer channels. | human |
| `number_checker_requires_paid_number` | 403 | The account needs an active non-sandbox channel to use number checks. | human |
| `number_checker_requires_non_sandbox_channel` | 403 | Run number checks on a non-sandbox channel. | fix |
| `pacing_not_available` | 409 | This setting is unavailable on this channel. | fix |
| `queue_full` | 429 | This channel's send queue is full; try again later. | retry |

What each "Do" means:

- **fix**: Fix the request. Sending it again unchanged gets the same answer.
- **auth**: Check the token and the channel ID. Do not loop: the same token gets the same answer.
- **human**: Stop and tell the person. Only the channel owner (console) or support can clear it.
- **inspect**: For `verification_failed`, get the group named in `group_jid`; never repeat the create. For `whatsapp_disconnected` or `whatsapp_timeout`, the response cannot tell whether the write was sent; treat any write as possibly applied; list or read the state of what you changed before retrying a write; never re-create (e.g. a group) without reading/listing first; reads can be retried after a short back-off.
- **wait**: Wait the `Retry-After` header (or `retry_after`, or until `resets_at`), then try again. Nothing was done.
- **wait_ambiguous**: Wait the `Retry-After` header, then read `ambiguous` in the body before you retry. If ambiguous is false, nothing was done. If ambiguous is true, the add may have gone through; check membership before retrying.
- **backoff**: Back off for minutes, not seconds, and slow down. Nothing was done.
- **retry**: Safe to retry a READ after a short wait. On a SEND, see the delivery-unknown rule before you retry.
- **unknown**: DO NOT RESEND. Read the chat's messages and look for the returned `id` first.
- **partial**: DO NOT RESEND the same request. Part of it was already done; the body says how much.

<!-- END GENERATED: errors-table -->

"retry" on a SEND does not mean send again: a 502 on a send is delivery
unknown. Read [send-once.md](send-once.md) first.

### The 429s are different things

All of these are HTTP 429, and none of them means "try again in a second" by
default.

<!-- BEGIN GENERATED: errors-429 (do not edit; run node tools/generate.mjs) -->

| Body schema | `code` | Fields beyond `code` and `error` | Retry-After header |
|---|---|---|---|
| RateLimitError | `rate_limited` | `window`, `retry_after` | yes |
| WhatsAppRateLimitError | `whatsapp_rate_limited` | none | no |
| DailySendCapError | `daily_send_cap_exceeded` | `window`, `retry_after`, `cap`, `sent`, `resets_at` | no |
| ActionCapError | pattern `^daily_cap_[a-z_]+$` | `class`, `window`, `retry_after`, `cap`, `sent`, `tier`, `resets_at` | no |
| SandboxAllowanceError | `sandbox_allowance_exceeded` | `window`, `retry_after`, `cap`, `used`, `reserved`, `resets_at` | yes |
| GatewayBusyError | `gateway_busy` | `bound`, `retry_after` | yes |
| CheckAllowanceError | pattern `undefined` | `retry_after`, `window`, `cap`, `used`, `resets_at` | no |
| HistoryRequestTooSoonError | `history_request_too_soon` | `retry_after` | no |
| QueueFullError | `queue_full` | none | no |

The spec on the header: "Seconds to wait. Sent with rate_limited, gateway_busy, sandbox_allowance_exceeded, checks_spaced_out and check_allowance_used."

<!-- END GENERATED: errors-429 -->

- `rate_limited`, `gateway_busy`, `sandbox_allowance_exceeded`: wait the
  `Retry-After`, then continue at a slower pace.
- `daily_cap_<class>` (warm-up protection on): stop that kind of action for
  today. `resets_at` says when it clears.
- `daily_send_cap_exceeded`: the operator stopped sends on this channel. Do not
  wait for `resets_at`; tell the person.
- `whatsapp_rate_limited`: WhatsApp throttled the number itself. Stop the loop,
  back off for minutes, and send less. Retrying fast makes it worse.

### Incorrect

```text
if status == 429: sleep(1) and retry
if status >= 500: retry up to 5 times
```

The first hammers a number WhatsApp is already throttling. The second resends a
message whose delivery is unknown.

### Correct

```text
switch body.code:
  send_unconfirmed            -> delivery unknown: read the chat, never resend
  rate_limited, gateway_busy  -> wait Retry-After, then slow down
  whatsapp_rate_limited       -> back off for minutes, send less
  daily_send_cap_exceeded     -> stop, tell the person
  not_linked, stood_down      -> stop, the person acts in the console
  default                     -> use the table above
```
