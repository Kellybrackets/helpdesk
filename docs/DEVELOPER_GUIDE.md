# Developer exploration guide

Start with `make seed`, log in as a Tier 1 Agent, inspect a demo ticket, and open the same ticket as its customer in another browser profile. Compare the fields, comments, reply controls and organization visibility. Then inspect the source paths below. This task makes no changes to those product systems.

| Area | Start here | What to inspect |
| --- | --- | --- |
| Ticket model | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` and `hd_ticket.py` | Fields, link types, lifecycle hooks, SLA application, permissions |
| Ticket creation | `helpdesk/helpdesk/doctype/hd_ticket/api.py`; ticket pages under `desk/src/pages/` | Portal/agent inputs, template validation, first Communication |
| Assignment | `helpdesk/api/ticket.py`, `helpdesk/api/assignment_rule.py`, `helpdesk/helpdesk/doctype/hd_team/hd_team.py` | `assign_agent`, native ToDo assignments, team rotation rules |
| Assignment customization | `helpdesk/overrides/assignment_rule.py`, `helpdesk/extends/assignment_rule.py` | Available agents and Helpdesk-specific rule validation |
| Statuses | `helpdesk/helpdesk/doctype/hd_ticket_status/`, `helpdesk/setup/install.py` | Agent/customer labels and Open/Paused/Resolved categories |
| SLA logic | `helpdesk/helpdesk/doctype/hd_service_level_agreement/` | Policy ranking, conditions, working hours, response/resolution clocks |
| Agent UI | `desk/src/router/index.ts`, `desk/src/pages/`, `desk/src/components/` | `TicketsAgent`/`TicketAgent` route components and shared ticket controls |
| Customer portal | Same router, `TicketsCustomer`/`TicketCustomer`/`TicketNew` routes | Customer layout, creation form and organization visibility |
| Notifications | `helpdesk/notifications.py`, `helpdesk/extends/notification_log.py`, `desk/src/components/notifications/` | In-app delivery, notification permission and realtime refresh |
| Email ingestion | `helpdesk/overrides/email_account.py`, Frappe Email Account and Communication controllers | Incoming routing, sender/contact matching and ticket updates |
| Replies/comments | `hd_ticket.py`, `helpdesk/api/timeline.py`, `helpdesk/api/comment.py`, `helpdesk/extends/comment.py` | Agent/customer Communication creation, private Comment visibility |
| Knowledge base | `helpdesk/api/knowledge_base.py`, `helpdesk/helpdesk/doctype/hd_article/`, `desk/src/pages/knowledge-base/` | Published versus draft access and public article routes |
| Saved replies | `helpdesk/helpdesk/doctype/hd_saved_reply/`, `helpdesk/api/saved_replies.py` | Global/team/personal scope and saved actions |
| Permissions | `helpdesk/hooks.py`, `helpdesk/utils.py`, controller permission functions | Roles, query restrictions, customer manager membership |
| API endpoints | `helpdesk/api/`, `@frappe.whitelist` methods in controllers | Arguments, permission checks, returned shapes, error handling |
| Integrations | `helpdesk/integrations/erpnext/`, Telephony app, `desk/src/pages/call-logs/` | Optional ERPNext sync and phone-provider integration |

Useful searches:

```bash
rg '@frappe.whitelist|def has_permission|def permission_query' helpdesk
rg 'reply_via_agent|create_communication_via_contact|assign_agent' helpdesk
rg 'TicketsAgent|TicketsCustomer|TicketNew' desk/src/router
```

## Request walkthrough

A customer submits a ticket in the Vue portal. The server validates the user/contact, inserts an HD Ticket, selects its status/priority/SLA, creates the initial Communication, and runs normal assignment hooks. Agent list resources fetch only allowed records. An agent reply creates a sent Communication; its hooks update first-response information. Status changes invoke the ticket/SLA lifecycle. Realtime events tell open clients to refresh.

A team is an assignment group. An HD Customer represents an organization or individual customer. Its Contact members link to portal User accounts. A customer manager may see organization tickets; an ordinary member normally sees their own permitted tickets. Agent comments are private; customer-visible replies are Communications. Do not assume frontend hiding enforces confidentiality.

## Working on a change later

Create `feature/<description>` from `dev`. Keep application changes small and separate from evaluation fixtures. Read `AGENTS.md` and any more specific instructions first. Use a fresh test site for automated backend tests and avoid running destructive test suites on a site with data you want to keep. Backend test helpers belong in `helpdesk/test_utils.py` per upstream conventions.

Run the appropriate upstream test modules for the affected controller and targeted browser tests from `e2e/`. `make verify` is a local integration smoke check; it is not a replacement for the full upstream suite. It performs real ticket writes and leaves a clearly named verification ticket for inspection.

`make build` updates frontend assets. `make migrate` applies DocType changes and patches. Restart the Bench container after dependency/config changes. Do not edit generated assets or make ad-hoc database schema changes as a development workflow.

## Demo fixtures and limits

The seed function is a Bench-only developer utility, not a whitelisted endpoint. It has explicit development/email guards and uses stable keys. Reruns preserve existing tickets, users, passwords, article edits and assignments. A partially completed run can be retried; individual completed tickets are committed so they are not lost when a later fixture fails.

Historical timestamps are synthetic and may coexist with current-time system activity. SLA counters are recalculated by native hooks and scheduler jobs, so overdue examples evolve with time. The service calendar covers a finite demo period. For a fresh historical demonstration, initialize a new evaluation site rather than overwriting engineers' existing changes.

The demo escalation team plus urgent SLA is an example of operational escalation using existing features. There is no new time-based escalation feature. Mail is muted, Telephony has no provider credentials, and ERPNext is not installed; actual external email, calls and ERPNext synchronization are not part of the smoke test.
