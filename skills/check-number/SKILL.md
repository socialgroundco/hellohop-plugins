---
name: check-number
description: Check to ensure numbers are still on WhatsApp, for your own contacts, using a background number check.
argument-hint: "<phone number> [more numbers]"
disable-model-invocation: true
---

# /hellohop:check-number

The pinned published MCP release does not yet include this tool. If it is
missing, stop and say the plugin needs the upcoming MCP release. Do not guess
a result, call REST instead, or send a probe message.

1. Call status and stop unless state is CONNECTED. On `not_configured`, give
   https://hellohop.app for setup; configure the token and channel ID locally
   and restart the agent. Never ask for a token in chat.

```json
{"tool": "channel_status", "arguments": {}}
```

2. With the new tool available, start one background check with 1 to 50 of the
   person's existing contact numbers, country code included:

```json
{"tool": "check_numbers", "arguments": {"numbers": ["<PHONE_WITH_COUNTRY_CODE>"]}}
```

A sandbox-only account returns 403 `number_checker_requires_paid_number`.
An eligible account using a sandbox channel returns 403
`number_checker_requires_non_sandbox_channel`. Explain the code and stop;
use an eligible non-sandbox channel. Never describe a refusal as a negative
WhatsApp result.

3. Report the returned job ID and state. A job is not a number result. Read a
   job later using its actual ID; do not start the same list again:

```json
{"tool": "check_numbers", "arguments": {"job_id": "<RETURNED_JOB_ID>"}}
```

Do not poll in a loop. Report progress, pause or failure as returned. Report
rows as registered, not_registered, invalid or error; never turn invalid,
pending or error into "not on WhatsApp". Checks are point-in-time answers and
can be wrong or out of date; they do not guarantee message delivery. Checks
are spaced out and a large list can take hours or days. This sends no message
to the contacts. Use your own contacts, never a bought or scraped list.
