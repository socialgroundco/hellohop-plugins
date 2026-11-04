---
title: Send text once, and never resend when delivery is unknown
impact: CRITICAL
impactDescription: A blind retry after a timeout sends the same message to a real person twice
tags: send, text, quoted, mentions, server_ack, send_unconfirmed, delivery, retry
---

## Send text once, and never resend when delivery is unknown

### The request

```http
POST /v1/sessions/<CHANNEL_ID>/messages/text
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"to": "XXXXXXXXXXX@s.whatsapp.net", "text": "Thanks, see you tomorrow", "quoted": "MESSAGE_ID"}
```

- `to` (required): a phone number in full international form, or a JID. See
  [addresses.md](addresses.md).
- `text`: the message.
- `mentions`: optional phone numbers or JIDs to tag. A number that cannot be
  used answers 403 `number_forbidden`.
- `quoted`: optional ID of a message this channel has in the same chat, to reply
  to it. An unknown one answers 400 `quote_not_found`; one from another chat
  answers 400 `quote_wrong_chat`.

The answer has `id`, `chat_jid`, `timestamp` and `status: "server_ack"`.
`server_ack` means WhatsApp's servers accepted the message. It is not a delivery
receipt. Delivered, read and played arrive later as `message.status` webhooks.

### Incorrect: invented fields

```http invalid unknown-field
POST /v1/sessions/<CHANNEL_ID>/messages/text
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"to": "XXXXXXXXXXX@s.whatsapp.net", "message": "Hi"}
```

Every body field not in the spec is refused with 400 `invalid_body`.

```http invalid missing-required
POST /v1/sessions/<CHANNEL_ID>/messages/text
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"text": "Hi"}
```

### The delivery-unknown rule

A send whose outcome you did not see may have gone out. Sending it again is how
the same message reaches a real person twice.

Delivery is UNKNOWN when any of these happens on a send:

1. No response arrived: a timeout, a dropped connection, a refused redirect.
2. A 504 with code `send_unconfirmed`. Its body has `ambiguous: true` and the
   `id` of the logged send.
3. Any 502 (an `upstream_` code). The edge answers 502 when the gateway did not
   answer in time, not only when it was never reached.
4. A 2xx whose body you could not read.
5. With the MCP server: a `send_text` result with `delivery: "unknown"`.

Then:

1. Do NOT send again. Do not retry automatically, now or later.
2. Read the chat: `read_messages` with the MCP server, or
   `GET /sessions/{name}/chats/{chat}/messages`. Look for the returned `id`, or
   for your text with `direction` `out`.
3. Found: it was sent. Carry on.
4. Not found: tell the person what happened and let them decide. A message log
   can lag, so absence is not proof it was not sent.

A 500 or 503 on a send is not on the list above, but you cannot prove from the
outside that nothing went out. Read the chat first; it costs one GET.

A 4xx (a 429 included) means the gateway refused before sending. Fix the request
or wait the `Retry-After`; nothing went out.

### Incorrect: a retry loop

```text
for attempt in 1..3:
    response = POST messages/text
    if response is not 200: sleep 2s and try again
```

A timeout on attempt 1 may already be a delivered message. This loop sends it up
to three times.

### Correct: classify, then act

```text
response = POST messages/text (client: no automatic retries, no redirects)
if 2xx with a readable body: done
if no response, 502, 504, or ambiguous true: delivery unknown, follow the rule above
if 429: nothing was sent; wait Retry-After (or tell the person, per errors.md)
if other 4xx: nothing was sent; fix the request
if 500 or 503: read the chat before deciding anything
```

Turn off automatic retries in your HTTP client for every POST, and do not follow
redirects.

### Parameters that do not exist

- `sendText`: `message`, `caption`, `media`, `buttons`, `typing_time`, `no_link_preview`, `view_once`, `ephemeral`

## Send only the message types the API has

The table below is generated from the spec. It lists the requests that send a
message or set read receipts, typing and presence. Reactions and deletes are in
the Choosing table further down.

<!-- BEGIN GENERATED: sendable (do not edit; run node tools/generate.mjs) -->

| Request | Sends |
|---|---|
| `POST /sessions/{name}/messages/contact` | Send a contact card |
| `POST /sessions/{name}/messages/group-invite` | Send a native group invite |
| `POST /sessions/{name}/messages/image` | Send an image |
| `POST /sessions/{name}/messages/video` | Send a video |
| `POST /sessions/{name}/messages/audio` | Send an audio file |
| `POST /sessions/{name}/messages/voice` | Send a voice note |
| `POST /sessions/{name}/messages/document` | Send a document |
| `POST /sessions/{name}/messages/poll` | Send a poll |
| `POST /sessions/{name}/messages/read` | Send read receipts |
| `POST /sessions/{name}/messages/text` | Send a text |
| `POST /sessions/{name}/presence` | Set presence |
| `POST /sessions/{name}/typing` | Show or clear the typing indicator |

<!-- END GENERATED: sendable -->

### Choosing

| The person wants to send | Use |
|---|---|
| Words, a link, a reply to a message | `POST /sessions/{name}/messages/text` (with `quoted` for a reply) |
| An add_request invitation card | `POST /sessions/{name}/messages/group-invite` |
| Someone's contact details as a card | `POST /sessions/{name}/messages/contact` |
| "Seen" ticks on messages they received | `POST /sessions/{name}/messages/read` |
| A typing indicator before a reply | `POST /sessions/{name}/typing` |
| A picture | `POST /sessions/{name}/messages/image` |
| A video clip | `POST /sessions/{name}/messages/video` |
| An audio file | `POST /sessions/{name}/messages/audio` |
| A recorded `voice` note | `POST /sessions/{name}/messages/voice` |
| A file such as a PDF | `POST /sessions/{name}/messages/document` |
| A question with answer options to vote on | `POST /sessions/{name}/messages/poll` |
| An emoji reaction to a message | `PUT /sessions/{name}/messages/{message}/reaction` (`DELETE` the same path removes it) |
| To delete a message it sent, for everyone | `DELETE /sessions/{name}/messages/{message}` |
| Anything else: stickers, GIFs, locations, buttons, lists, carousels, edits, forwards, status updates, newsletters, calls | Tell the person the API does not send it yet |

### Not available through the API

Stickers, GIFs, locations, buttons, lists, carousels, edits, forwards, status
updates, newsletters and calls. Do not fake one: a "list" typed out as numbered
text is a different thing, so ask the person before you substitute.

#### Incorrect

```http invalid unknown-method
POST /v1/sessions/<CHANNEL_ID>/messages/sticker
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"to": "XXXXXXXXXXX@s.whatsapp.net", "media": "https://example.com/a.webp"}
```

### A contact card

```http
POST /v1/sessions/<CHANNEL_ID>/messages/contact
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"to": "XXXXXXXXXXX@s.whatsapp.net", "display_name": "Front desk", "vcard": "BEGIN:VCARD\nVERSION:3.0\nFN:Front desk\nTEL:+XXXXXXXXXXX\nEND:VCARD"}
```

All three fields are required. A contact card is a send: the delivery-unknown
rule in [send-once.md](send-once.md) applies to it too.

### Typing and presence

```http
POST /v1/sessions/<CHANNEL_ID>/typing
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"chat": "XXXXXXXXXXX@s.whatsapp.net", "state": "typing"}
```

```http invalid enum
POST /v1/sessions/<CHANNEL_ID>/presence
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"presence": "busy"}
```

Every allowed `state` and `presence` value is listed in
[start-here.md](start-here.md).

### Receiving

Inbound messages can be of more types than you can send.

<!-- BEGIN GENERATED: inbound-types (do not edit; run node tools/generate.mjs) -->

Inbound `type` values (on a `message` webhook and in listed messages): `text`, `image`, `video`, `document`, `audio`, `sticker`, `contact`, `location`, `poll`, `poll_vote`, `reaction`, `short`, `group_invite`, `live_location`, `contact_list`, `protocol`, `unknown`.

<!-- END GENERATED: inbound-types -->

A message with media carries a `media_id`. Download it with
`GET /sessions/{name}/media/{id}`; it is always served as
`application/octet-stream`. A `protocol` message is WhatsApp housekeeping, not
something a person wrote: a bot should not answer it.

### Parameters that do not exist

- `sendContact`: `contacts`, `phone`, `full_name`
- `setTyping`: `duration`, `typing_time`
- `setPresence`: `chat`, `status`

Native group invites require `to` (a person), `group` (a `@g.us` JID), non-empty `group_name` and `code`, and a future `expiration` in Unix seconds from the participant add result. `caption` is optional. They return the usual send result and use the same admission and sandbox allowance. Acceptance uses the existing `group.participants` webhook.
