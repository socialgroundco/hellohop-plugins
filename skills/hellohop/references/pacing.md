---
title: Pace sends yourself, go slow on new chats, and know what warming is not
impact: CRITICAL
impactDescription: Sending to people who did not ask to hear from you can get a number restricted by WhatsApp, and that cannot be undone from the API
tags: pacing, rate limits, new chats, sandbox, warming, warm-up protection, stood_down
---

## Pace sends yourself, go slow on new chats, and know what warming is not

### How sending works on a paid channel

A paid channel has no daily message allowance. HelloHop sends what you send, and answers 429 (`rate_limited`, `gateway_busy`) when the API itself is busy. WhatsApp sets its own rules for each number.

Suggested starting point (our guidance, not a gateway limit and not a WhatsApp
rule):

- Put a random gap between sends, for example tens of seconds, never a fixed
  interval. Never loop as fast as the API answers.
- Send in small batches with long, irregular pauses between them.
- Prefer replies. A message to someone who wrote to you is the safest send.
- On a new number, start with a handful of new chats a day and raise it slowly
  over weeks.
- Read `GET /sessions/{name}/safety` between batches and stop on `bad`.

### New chats are the risky ones

A first message to someone who has never talked to the number is what WhatsApp
watches most.

- Check only the numbers you are about to message, never a bought or scraped
  list (`POST /sessions/{name}/contacts/check`, at most 50 per call).
- For a longer list, start a number check (`createNumberCheck`, or the MCP tool
  `check_numbers`). It runs in the background, spaced out, with a daily check allowance
  set by the number's age, and answers repeats from a cache.
  Checks require an active non-sandbox channel and cannot run on the sandbox.
- Saving a contact before you message them helps the Saved contacts reading.
  Saving people in bulk that you never message does not.
- Adding people to groups on a new number is the riskiest action of all. Keep it
  low.

#### Incorrect

```text
for number in 5000_numbers_from_a_spreadsheet:
    POST contacts/check
    POST messages/text  "Special offer!"
```

#### Correct

```text
for person in today's_small_batch (people who expect the message):
    POST messages/text
    wait a random gap
check safety; stop on bad
```

### The sandbox channel

Every account has one free sandbox channel (`plan` is `sandbox`) for testing.

<!-- BEGIN GENERATED: sandbox-allowances (do not edit; run node tools/generate.mjs) -->

The spec: "A sandbox channel reached one of its allowances (180 messages a day, 10 new chats a month, 5 group adds a day, 1,500 API calls a month; days and months in Bangkok time, UTC+7). Every request made with the sandbox channel's key counts as an API call, reads included. Sent with a Retry-After header. Paid channels never receive it."

The `window` values:

- `sandbox_messages_daily`
- `sandbox_chats_monthly`
- `sandbox_group_adds_daily`
- `sandbox_api_calls_monthly`

<!-- END GENERATED: sandbox-allowances -->

A request that would go over an allowance is refused whole, before anything is
sent. A chat already messaged this month does not count again.

### Warm-up protection

An optional console switch, reported as `warmup_protection` on the channel.
When on, group adds, group and community creation, contact checks and contact saves have daily allowances that grow with the number's age. Over one, the call
answers 429 with `code` `daily_cap_<class>`, the `class`, the `tier` and
`resets_at`. Stop that kind of action for the day. The number checker's own spacing and check allowance apply whether this switch is on or off.

### Warming is on by default

Warming is on by default for every channel, at no extra cost. The warming endpoint answers 404 `not_found` only when an operator has switched warming off for that channel or restricted it. Do not build your own warming. `daily_send_cap` applies to sandbox channels only.

### When WhatsApp pushes back

- `whatsapp_rate_limited` (429): WhatsApp throttled the number. Back off for
  minutes and send less.
- `stood_down` (409): "No: WhatsApp stood this number down".
  "WhatsApp stood this number down. It cannot send until it is linked again."
- `daily_send_cap_exceeded` (429): the operator stopped sends. Tell the person.

### Parameters that do not exist

- `sendText`: `delay`, `schedule_at`, `priority`
- `updateChannel`: `warming`, `daily_send_cap`, `warmup_protection`

### Health, with evidence

The readings, by key: `stood_down`, `lifetime`, `address_book_coverage`, `response_rate`, `proxy`.
Channel-token view returns 4 rows (no proxy); operator and owning-account view returns 5.
Levels on the wire: `good | watch | bad | too_early`. The `overall` level is always `good | watch | bad`; waiting/stale reads `watch` unless a measured reading is `bad`.
A sample too small to judge gets a neutral "Too early" level: good plus too_early reads good when at least one reading is measured good; all too_early reads watch ("Not enough data yet"); a reading that could not be measured reads watch.
A fault (unreadable, faults > 0) never yields too_early or GOOD; it yields WATCH with data.unreadable true and value "Could not read". A measured BAD stands.
Every indicator carries evidence_at (nullable) and live.
Health reports existing refusals and adds no restrictions. Only severe WhatsApp logout records affect restriction history; operator and phone unlinks do not. Relinking clears that history.

For `lifetime`, a computed age has an empty `value`. Use the `source`,
`linked_at`, `days` and `is_lower_bound` fields of `data` to render it. A
`registration_date` source is a calendar date encoded as UTC midnight; preserve
that date rather than converting it to a local instant. Pairing and message
timestamps are instants and use the viewer's zone. Count calendar days to
`measured_at` in the viewer's zone; lower-bound ages use the `days` field.

The lifetime reading is good or watch, never bad: a young number is something to watch, not something wrong.

Only a reading about the number's state right now can be bad: stood down, or a failing proxy. Age, contacts, replies and a missing or shared proxy are things to watch.

For `stood_down`, the `refused` field of `data` is the policy-only refusal used by the warmer,
independent of the Health `level`. Cap refusals and recent restriction history
can change the Health level without changing this field. The `stood_down`,
`blocked`, `quarantined` and optional `since` fields keep their previous meanings.
The warmer still treats an allowed verdict beside one of those conditions as
unreadable.
