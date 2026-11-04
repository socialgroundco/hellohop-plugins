---
title: Receive with signed webhooks, never by polling
impact: HIGH
impactDescription: Polling misses messages and burns requests; an unverified webhook lets anyone inject fake messages
tags: webhooks, receive, signature, hmac, retries, polling, events
---

## Receive with signed webhooks, never by polling

### Why not poll

`GET /sessions/{name}/chats` returns up to 100 chats, with no paging and no
query string. `GET /sessions/{name}/chats/{chat}/messages` returns 50 messages
by default (`limit` 1 to 500) and pages with `before`, set to the previous
page's `next_before`. Both read the gateway's own log of this channel, which
holds only what it saw while connected. A poll loop misses whatever the log
never saw, and every poll is load on a real number's channel.

#### Incorrect

```http invalid query-string
GET /v1/sessions/<CHANNEL_ID>/chats/XXXXXXXXXXX@s.whatsapp.net/messages?limit=500&since=yesterday
Authorization: Bearer <CHANNEL_TOKEN>
```

Use the lists to look something up once, for example to check a send whose
delivery is unknown. Use webhooks for everything that arrives.

### Set the receivers

```http
PUT /v1/sessions/<CHANNEL_ID>/webhooks
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"receivers": [{"url": "https://example.com/hooks/whatsapp", "events": ["message", "message.status"], "secret": "<AT_LEAST_24_RANDOM_CHARACTERS>"}]}
```

- A receiver takes `url`, `events` and `secret`, nothing else.
- `secret` needs at least 24 characters. Always set one; it is the only way to
  know a delivery came from the gateway. Keep it on your server.
- Up to 8 receivers per channel.
- On an existing URL, omit `events` to keep its stored subscription. On a new
  URL, omission uses the gateway defaults. Send `events: []` to reset to those
  defaults. A misspelled event name is accepted and matches nothing, so copy
  names from the table below.
- PUT replaces the whole list. Read it first (`GET /sessions/{name}/webhooks`)
  and send back the receivers you want to keep, or you delete them. An empty
  list removes every receiver; that answers 403 `admin_only_field` when one of
  them carries a media setting made in the console.
- GET never returns a secret, only `secret_set`. It also returns `persistent`
  and `persistence_note`, which say how deliveries are stored.

#### Incorrect

```http invalid min-length
PUT /v1/sessions/<CHANNEL_ID>/webhooks
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"receivers": [{"url": "https://example.com/hooks/whatsapp", "secret": "short"}]}
```

```http invalid unknown-field
PUT /v1/sessions/<CHANNEL_ID>/webhooks
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"receivers": [{"url": "https://example.com/hooks/whatsapp", "secret": "<AT_LEAST_24_RANDOM_CHARACTERS>", "headers": {"X-Key": "abc"}}]}
```

### Test it

```http
POST /v1/sessions/<CHANNEL_ID>/webhooks/test
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"url": "https://example.com/hooks/whatsapp"}
```

The `url` must be one you configured. One signed attempt, nothing sent to
WhatsApp. The test delivery's type is `webhook.test`, which is not one of the
event types below, so let your handler accept and ignore it. Sending the test
again too soon answers 429 `rate_limited`.

### What arrives

Each event is one POST per receiver, with headers `X-HelloHop-Event` (the type),
`X-HelloHop-Delivery` (the body `id`, unsigned, informational) and `X-HelloHop-Signature`. The body is
`{"id", "type", "session", "timestamp", "payload"}`.

<!-- BEGIN GENERATED: webhook-events (do not edit; run node tools/generate.mjs) -->

| Event `type` | Payload fields (optional ones are absent, never empty) |
|---|---|
| `message` | `id`, `chat_jid`, `sender_jid`, `push_name` (optional), `type`, `text` (optional), `media_id` (optional), `from_me`, `is_group`, `timestamp`, `mentions` (optional), `quoted_id` (optional), `quoted_author` (optional), `sender_lid` (optional), `sender_pn_resolved` (optional), `chat_lid` (optional), `chat_pn_resolved` (optional), `poll` (optional), `reaction` (optional), `revoke` (optional) |
| `group.participants` | `group_jid`, `action`, `participants`, `participant_lids` (optional), `participants_pn_resolved` (optional), `actor_jid` (optional), `timestamp` |
| `session.status` | `state`, `jid` (optional), `reason` (optional), `timestamp` |
| `message.status` | `ids`, `chat_jid`, `recipient_jid` (optional), `status`, `timestamp` |

`message.status` `status` values: `delivered`, `read`, `played`, `undecryptable`.
`session.status` `state` values: `NEW`, `PAIRING`, `CONNECTED`, `DISCONNECTED`, `BLOCKED`.

<!-- END GENERATED: webhook-events -->

`mentions` absent means the message carried no context to read; `[]` means it
tagged nobody. A message you sent from the phone itself arrives with `from_me`
true.

### Verify the signature before you trust the body

`X-HelloHop-Signature` is the lowercase hex HMAC-SHA256 of the RAW request body,
keyed with the receiver's secret, with no prefix. Compute it over the bytes you
received, before parsing JSON.

```js
import { createHmac, timingSafeEqual } from 'node:crypto';

export function signatureOk(rawBody, signatureHeader, secret) {
  const expected = Buffer.from(createHmac('sha256', secret).update(rawBody).digest('hex'));
  const given = Buffer.from(signatureHeader ?? '');
  return given.length === expected.length && timingSafeEqual(given, expected);
}
```

Reject a delivery whose signature does not match, and never act on its text.

### Retries and duplicates

- An event is stored before it counts as handled, then delivered until your
  endpoint answers 2xx.
- Failed deliveries retry with a growing wait, up to an hour apart, at least 50
  times (about two days), then the event is kept aside, not dropped.
- Delivery is at least once, not exactly once. A retry can repeat an event, so
  your receiver can see the same event more than once.
- For a `message` event, use the message `id` in the payload as the
  idempotency key.
- A retry keeps the same body `id`. The header is unsigned, so record the verified body `id`s you handled and
  skip repeats, so a retry never makes your bot reply twice.
- Answer 2xx fast and do the work afterwards. A slow handler looks like a failure
  and gets the event again.

### Parameters that do not exist

- `setWebhooks`: `webhooks`, `webhook_url`, `headers`, `retries`, `mode`
- `listChatMessages`: `limit`, `before`, `cursor`, `page`, `since`
- `listChats`: `limit`, `offset`, `unread_only`
