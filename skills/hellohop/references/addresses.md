---
title: Use the right chat ID, and put it in the path as written
impact: CRITICAL
impactDescription: A wrong chat ID sends to nobody or to the wrong person; a percent-encoded one is refused
tags: chat-id, jid, lid, to, phone, group, g.us, s.whatsapp.net
---

## Use the right chat ID, and put it in the path as written

WhatsApp addresses everything by a JID: `<user>@<server>`. The gateway uses
three forms.

| Chat | Form | Where you get it |
|---|---|---|
| A person | `XXXXXXXXXXX@s.whatsapp.net` | Their number: country code and digits, no `+`, no spaces, no device suffix |
| A group | `120363XXXXXXXXXXXX@g.us` | `GET /sessions/{name}/groups`, the `jid` of a created group, or a webhook's `chat_jid` |
| A community | `120363XXXXXXXXXXXX@g.us` | Same as a group: a community is a group with `is_community` true |

A group ID cannot be built from its name or its invite link. Read it from the
API.

### Sending: `to` is forgiving, a path is not

In a send body, `to` takes a phone number in full international form
(`+XXXXXXXXXXX` or `XXXXXXXXXXX`) or a JID. The gateway turns a number into a
person JID for you.

```http
POST /v1/sessions/<CHANNEL_ID>/messages/text
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"to": "+XXXXXXXXXXX", "text": "Your table is ready"}
```

In a URL path (`{chat}`, `{group}`, `{community}`, `{who}`), send the JID as
written. The API refuses any path containing `%`, so never percent-encode it.
Only letters, digits and `@ . : _ + -` are safe in a path segment.

#### Incorrect

```http invalid percent
GET /v1/sessions/<CHANNEL_ID>/chats/XXXXXXXXXXX%40s.whatsapp.net/messages
Authorization: Bearer <CHANNEL_TOKEN>
```

#### Correct

```http
GET /v1/sessions/<CHANNEL_ID>/chats/XXXXXXXXXXX@s.whatsapp.net/messages
Authorization: Bearer <CHANNEL_TOKEN>
```

### Old and wrong forms

- `XXXXXXXXXXX@c.us` is an old form. Use `@s.whatsapp.net`.
- `XXXXXXXXXXX:12@s.whatsapp.net` carries a device suffix. People are always
  addressed without one, so the same person always has the same address.
- A person JID ending in `@g.us`, or a group ID ending in `@s.whatsapp.net`,
  addresses nothing.

### LIDs: when WhatsApp hides the number

WhatsApp sometimes addresses a person by a LID (`<digits>@lid` or
`<digits>@hosted.lid`) instead of their number. The gateway publishes the phone
JID whenever it knows it:

- `sender_jid`, and `chat_jid` for a chat that is not a group, carry the phone
  JID. The LID the message arrived as is in `sender_lid` or `chat_lid`.
- When no number is known, the field keeps the LID and `sender_pn_resolved` or
  `chat_pn_resolved` is present and `false`. Treat that value as unresolved:
  never store it as a phone number.
- In `group.participants` events, `participant_lids` and
  `participants_pn_resolved` line up with `participants` by index.

Key your own records by the phone JID, and keep the LID beside it.

### Not supported

Newsletters (WhatsApp Channels), status updates and broadcast lists have no
endpoints. Do not build `@newsletter` or `@broadcast` IDs.

### Parameters that do not exist

- `sendText`: `chat_id`, `phone`, `jid`, `recipient`
- `listChatMessages`: `chat_id`, `phone`

## Manage groups, communities and contacts without guessing outcomes

Every route, field and limit is in [start-here.md](start-here.md). The rules
below are the ones agents get wrong.

### Groups

- List with `GET /sessions/{name}/groups`; read one with
  `GET /sessions/{name}/groups/{group}`. Group IDs come from here.
- Create with `POST /sessions/{name}/groups`: `subject` (1 to 25 characters),
  optional `participants` (at most 50) and optional `parent_jid` to create it
  inside a community.
- `PUT .../subject`, `PUT .../description` (an empty string removes it) and
  `PUT .../settings` change one thing each.

```http
PUT /v1/sessions/<CHANNEL_ID>/groups/120363XXXXXXXXXXXX@g.us/settings
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"locked": true, "member_add_mode": "admin_add"}
```

### Participants: add, remove, promote, demote

```http
POST /v1/sessions/<CHANNEL_ID>/groups/120363XXXXXXXXXXXX@g.us/participants
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"action": "add", "participants": ["XXXXXXXXXXX@s.whatsapp.net"]}
```

Each person gets a result with a `status`: `ok`, `error_<status>`, or `unknown`.
`unknown` means the gateway could not tell which person an answer belongs to,
and the change MAY have applied. Read the group before you retry, or you add
someone twice or remove the wrong person.

#### Incorrect

```http invalid enum
POST /v1/sessions/<CHANNEL_ID>/groups/120363XXXXXXXXXXXX@g.us/participants
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"action": "invite", "participants": ["XXXXXXXXXXX@s.whatsapp.net"]}
```

There is no invite action. To invite, get the link with
`GET /sessions/{name}/groups/{group}/invite-link` and send it as text.

```http invalid max-length
POST /v1/sessions/<CHANNEL_ID>/groups
Authorization: Bearer <CHANNEL_TOKEN>
Content-Type: application/json

{"subject": "Weekend running club members group"}
```

### Communities

A community is a group with `is_community` true. Create one, then create
subgroups in it or link existing groups (`POST .../links` with `group_jid`).

A subgroup create that answers 409 `verification_failed` DID create the
subgroup: its ID is in `group_jid`, and `retry_as_ambiguous` is false. Read it;
never create it again.

### Contacts

- `POST /sessions/{name}/contacts/check` with `phones` (1 to 50) checks to ensure
  numbers are still on WhatsApp. Use it to keep your own contacts current.
- `PUT /sessions/{name}/contacts/{who}` saves a contact; `full_name` is
  required. Save people you will message, not a whole list.
- `GET /sessions/{name}/contacts/{who}` reads one.
- `DELETE /sessions/{name}/contacts/{who}` removes one, through the same
  queue as a save. It is safe to repeat; `handset` reads `removed` once the
  phone confirmed it. On a halted channel it behaves as a save does: nothing
  is sent and `handset` is `failed`. A removal that was queued waits until an
  operator clears the halt; one that could not be queued (no phone number known
  yet, a full queue, or the enqueue itself failed) is not made, so send it
  again once the halt is cleared.

### Check to ensure numbers are still on WhatsApp

For one call's worth (at most 50) use `checkContacts`; it answers at once. For a longer list start a number check with
`createNumberCheck` (`POST /sessions/{name}/number-checks`, `numbers`, optional
`refresh`) or, over MCP, `check_numbers`. It runs in the background on the
channel's own connected non-sandbox number and keeps going without you.
The number checker is included with every paid number. Your account needs an
active non-sandbox channel, including a paid, complimentary, promotional or admin
grant. Otherwise the API returns 403 `number_checker_requires_paid_number`. A
sandbox request from an eligible account returns 403
`number_checker_requires_non_sandbox_channel`.

- Checks run in the background and are spaced out, and each number has a daily check allowance, so a long list can take hours or days. There is no setting to make a check faster.
- Read it with `getNumberCheck`: `state`, `done` of `total`, `budget` (check allowance), `eta` and `pause`.
  A `paused` check says why in `pause` and resumes by itself at `pause.resume_at`. That is not an error: do not poll in a loop and do not start the same list again.
  Only `channel_down` waits for you (`resumeNumberCheck`, once the channel is connected).
  Resolve an `account_suspended` pause before continuing. A failed check reports its code and reason in `failure`
  (`check_failed` for an upstream failure); it does not mean a number is unregistered.
- Read the rows with `getNumberCheckResults` (`offset`, `limit`, `status`),
  partial results included. A row is `registered`, `not_registered`, `invalid`
  (kept with its reason, never dropped), `error` (WhatsApp gave no answer; not
  the same as not registered) or `pending`.
- Rows carry `phone_e164` and `country` (the number actually checked), `jid`,
  `lid`, `is_business`, `verified_name`, `checked_at`, and `cached` with
  `age_seconds`. `is_business` appears only when `true`: omitted means not known
  to be a verified business, never personal.
- A repeat of a number checked recently is served from a cache (7 days if it is
  on WhatsApp, 24 hours if not) without asking WhatsApp; `refresh` asks again.
- A check is a point-in-time answer and can be wrong or out of date by the time
  you use it. It is not a guarantee that a message will be delivered.

### Pace these too

Group adds, group and community creation, contact checks and contact saves are
the actions WhatsApp reads most closely on a new number. With warm-up protection
on they have daily allowances (`daily_cap_<class>`), and the sandbox channel
counts group adds. See
[pacing.md](pacing.md).

### Parameters that do not exist

- `changeParticipants`: `invite`, `phones`, `participant`
- `createGroup`: `title`, `description`, `picture`
- `checkContacts`: `numbers`, `contacts`
- `saveContact`: `phone`, `last_name`
