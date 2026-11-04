---
title: Build a reply bot from webhooks, one reply per message
impact: MEDIUM
impactDescription: A bot that answers its own messages, retries, or fans out turns one inbound message into a burst
tags: bot, auto-reply, webhook, from_me, typing, read receipts
---

## Build a reply bot from webhooks, one reply per message

### The loop

1. Receive the webhook. Verify `X-HelloHop-Signature` over the raw body (see
   [receive.md](receive.md)). Reject a bad one.
2. Answer 2xx at once. Do the work after.
3. Skip an event `id` (from the verified body, not the unsigned `X-HelloHop-Delivery` header) you already handled.
4. Act only on `type` `message` with payload `from_me` false. Ignore your own
   sends, `protocol` messages and the `webhook.test` delivery.
5. Decide whether to answer. In a group (`is_group` true), answer only when the
   bot is tagged or the person asked for it.
6. Optionally mark it read and show typing.
7. Send ONE reply, quoting the message. Classify the result per
   [send-once.md](send-once.md); never retry an unknown delivery.

### Mark read and show typing

```http
POST /v1/sessions/<CHANNEL_ID>/messages/read
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"chat": "XXXXXXXXXXX@s.whatsapp.net", "message_ids": ["MESSAGE_ID"]}
```

Pass the `chat_jid` from the webhook. The gateway marks each ID read in the chat
it actually arrived in, so a phone JID works even when the message came under a
LID. The answer says how many were marked (`receipted`), and lists `skipped` IDs.

```http
POST /v1/sessions/<CHANNEL_ID>/typing
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"chat": "XXXXXXXXXXX@s.whatsapp.net", "state": "typing"}
```

### Reply

```http
POST /v1/sessions/<CHANNEL_ID>/messages/text
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"to": "XXXXXXXXXXX@s.whatsapp.net", "text": "Got it, we open at 9.", "quoted": "MESSAGE_ID"}
```

### Incorrect

```text
on webhook(message):
    POST messages/text to message.chat_jid
```

This answers its own sends (`from_me`), answers again on every redelivery, and
answers every group message.

### Correct

```text
on webhook(raw, headers):
    if not signatureOk(raw, headers.signature, secret): return 401
    respond 200 now
    if seen(headers.delivery): return
    event = parse(raw)
    if event.type != "message" or event.payload.from_me: return
    if event.payload.type == "protocol": return
    reply = decide(event.payload)
    if reply: send once, quoted; on unknown delivery, read the chat, never resend
```

Keep the bot's own pace: one reply per inbound message, a short human-like
pause before it, and no follow-up messages it was not asked for.

### Parameters that do not exist

- `markRead`: `read`, `all`, `chat_id`
- `sendText`: `reply_to`, `in_reply_to`, `context`
