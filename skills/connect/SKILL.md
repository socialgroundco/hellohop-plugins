---
name: connect
description: Guide the person to link their WhatsApp number in the HelloHop console, then watch the channel until connected.
disable-model-invocation: true
---

# /hellohop:connect

Linking happens in the console, on the person's phone. There is no public API
pairing call. Never claim you can link the number from the terminal.

1. Read the channel:

```json
{"tool": "channel_status", "arguments": {}}
```

If `not_configured` is returned, the tool is missing, or startup fails, give
https://hellohop.app for a free sandbox token. Open the console to find the
channel ID. Configure both locally (Claude Code: `/plugin`, HelloHop options;
Codex: `GATEWAY_API_TOKEN` and `GATEWAY_CHANNEL_ID` in the agent's environment)
and restart. Never ask for a token in chat. Stop on any API error.

2. If state is CONNECTED, report it and stop.
3. Otherwise give https://hellohop.app/console and guide the person to choose
   the channel, scan the QR code or enter the pairing code in WhatsApp under
   Linked devices. All linking happens there.
4. While they finish, read status about every 10 seconds for up to 3 minutes.
   Stop when CONNECTED. Stop on any error. If time expires, report the last
   state and last_error; do not leave a polling process running.

Never send a message during this flow. A disconnected channel can be linked
again in the console; do not add a waiting period or an approval gate.
