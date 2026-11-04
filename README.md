# HelloHop plugin for Claude Code and Codex

Read and send WhatsApp messages from your coding agent through
[HelloHop](https://hellohop.app), an independent WhatsApp API. The bundle has
the `hellohop` skill, send / check-number / connect commands and a stdio MCP server.
HelloHop is not affiliated with WhatsApp or Meta. Link your own number in the console.

## Release status

This plugin repository is published. Its MCP launch files pin
`hellohop-mcp@0.3.3`. That release starts without credentials and includes
`check_numbers`. The check-number command stops if its tool is unavailable.

## Claude Code

Claude Code 2.1.292 or later:

```sh
claude plugin install hellohop --marketplace socialgroundco/hellohop-plugins
```

The plugin offers channel token and channel ID options. You can leave them blank
and configure them later in `/plugin`. The sensitive token option uses Claude
Code's secure credential store. Get a free sandbox token at https://hellohop.app.
Never paste credentials into an agent conversation.

## Codex

Add the self-hosted marketplace:

```sh
codex plugin marketplace add socialgroundco/hellohop-plugins
```

Restart the desktop app, choose the HelloHop marketplace in the Plugins
Directory and install HelloHop. The bundle uses portable `plugin.json`,
`mcp.json`, and `skills/`. This stdio bundle is distributed through our own
marketplace; it is not a listing in the universal plugin directory.

Set `GATEWAY_API_TOKEN` and `GATEWAY_CHANNEL_ID` locally, then explicitly forward them with `env_vars` in the project's `.codex/config.toml` ([Codex MCP docs](https://learn.chatgpt.com/docs/extend/mcp)):

```toml
[plugins."hellohop@hellohop".mcp_servers.hellohop]
enabled = false
[mcp_servers.hellohop]
command = "npx"
args = ["-y", "hellohop-mcp@0.3.3"]
env_vars = ["GATEWAY_API_TOKEN", "GATEWAY_CHANNEL_ID"]
```

This keeps the plugin's skill and commands and uses the explicitly configured MCP server instead of the bundled copy. Restart Codex after configuring it.

Sending is off by default. To opt in explicitly, set `GATEWAY_ALLOW_SEND=1` yourself in the environment you start Codex from, then replace the `env_vars` line above with this line and restart Codex:

```toml
env_vars = ["GATEWAY_API_TOKEN", "GATEWAY_CHANNEL_ID", "GATEWAY_ALLOW_SEND"]
```

For the MCP server alone, without the bundled skill and commands:

```sh
codex mcp add hellohop --env GATEWAY_API_TOKEN=<token> --env GATEWAY_CHANNEL_ID=<channel> -- npx -y hellohop-mcp@0.3.3
```

Replace the placeholders locally.

## Commands

Claude Code exposes these as `/hellohop:send`, `/hellohop:check-number` and
`/hellohop:connect`. In Codex, invoke the matching installed skill.

- send: checks status and safety, shows the exact recipient and text for approval,
  and sends once. If sending is off, it prints the line to enable it yourself.
- check-number: checks to ensure numbers are still on WhatsApp, for your own
  contacts. Requires the upcoming MCP release, an eligible account and a
  connected non-sandbox channel. Sandbox-only accounts receive 403. Results
  arrive through background jobs; a check can be wrong or out of date.
- connect: guides you to https://hellohop.app/console to link your phone,
  then watches status for at most 3 minutes. Pairing happens in the console.

## Enable per project

A plugin's MCP server runs in every session where the plugin is enabled.
Enable it only in projects that need WhatsApp. In Claude Code, use project
scope in `/plugin`. In Codex, enable `hellohop@hellohop` in the project's
`.codex/config.toml`:

```toml
[plugins."hellohop@hellohop"]
enabled = true
```

Sending is off by default. To opt in, set `GATEWAY_ALLOW_SEND=1` yourself in
the environment you start the agent from, then restart. The commands never
enable it for you. Number checks are available independently of that send gate;
they start a background job and are not annotated as read-only.

Messages from other people can contain instructions aimed at your agent.
Do not enable sending in a session that reads messages from people you do not
trust. Approve each send after reviewing exactly what it will do. Never resend
when delivery is unknown.

## Before publication

Run `python3 scripts/sweep.py` from this bundle. It scans hidden files too,
reports a planted positive control, then reports the file and forbidden-hit
counts. A nonzero result blocks publication. Explicit paths can scan other
public surfaces too. Run its tests with
`python3 -m unittest discover -s scripts -p test_sweep.py`.

MIT licensed.
