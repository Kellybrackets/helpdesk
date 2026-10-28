"""Opt-in development fixtures. Run with bench execute helpdesk.demo.seed.run."""

import os
from datetime import timedelta

import frappe
from frappe.utils import now_datetime

AGENTS = [
    ("support.admin", "Support Admin", ["Agent", "Agent Manager", "System Manager"]),
    ("tier1", "Tier 1 Agent", ["Agent"]),
    ("tier2", "Tier 2 Agent", ["Agent"]),
    ("technical", "Technical Support Agent", ["Agent"]),
    ("manager", "Service Manager", ["Agent", "Agent Manager"]),
]
COMPANIES = [
    ("Cedar Finance Demo", "cedar"),
    ("Copper Retail Demo", "copper"),
    ("Cloudline Telecom Demo", "cloudline"),
    ("Meadow Public Services Demo", "meadow"),
    ("Maple Advisory Demo", "maple"),
]
SCENARIOS = [
    (
        "Unable to log into account",
        "Bug",
        "Access",
        "The sign-in page loops after entering the verification code. Three staff members are affected.",
        "Cleared the stale session and confirmed sign-in from a fresh browser profile.",
    ),
    (
        "Invoice incorrectly generated",
        "Bug",
        "Billing",
        "The latest monthly invoice includes a retired service. Please review the demo invoice INV-1042.",
        "Removed the retired line item and regenerated the sample invoice.",
    ),
    (
        "Payment not reflecting",
        "Incident",
        "Billing",
        "A test payment completed yesterday but the sandbox balance still shows outstanding.",
        "Replayed the sandbox payment callback and reconciled the balance.",
    ),
    (
        "User permissions problem",
        "Question",
        "Access",
        "Our new analyst can view dashboards but cannot export the weekly report.",
        "The company administrator granted the approved reporting role.",
    ),
    (
        "System running slowly",
        "Incident",
        "Performance",
        "Search takes approximately 20 seconds during the morning shift for our regional office.",
        "Removed an inefficient filter and verified the response time is under two seconds.",
    ),
    (
        "API integration error",
        "Bug",
        "Integration",
        "The nightly sandbox synchronization returns HTTP 422 for records with empty department codes.",
        "Updated the sample payload to omit empty optional department codes.",
    ),
    (
        "Data export request",
        "Question",
        "Reporting",
        "Please explain how to export the previous quarter's support activity as CSV.",
        "Provided export steps and verified the downloaded file contains the requested date range.",
    ),
    (
        "Password reset",
        "Question",
        "Access",
        "A demo user has lost access to their password manager and needs the reset procedure.",
        "The user completed the reset procedure and confirmed successful login.",
    ),
    (
        "Account configuration issue",
        "Question",
        "Configuration",
        "Our organization needs separate notification preferences for billing and technical contacts.",
        "Updated the notification preferences and confirmed each contact's settings.",
    ),
    (
        "Service unavailable",
        "Incident",
        "Availability",
        "The sandbox status endpoint returns 503 and our test users cannot load their dashboard.",
        "Restarted the failed sandbox service and confirmed recovery with health checks.",
    ),
    (
        "Duplicate transaction",
        "Bug",
        "Billing",
        "Retrying a test checkout produced two transaction records with the same reference.",
        "Removed the duplicate sandbox entry and documented the idempotency key requirement.",
    ),
    (
        "Feature setup question",
        "Question",
        "Configuration",
        "We need guidance on setting up a shared queue for requests from multiple branches.",
        "Configured a sample team queue and demonstrated the assignment rotation.",
    ),
    (
        "Integration credentials expired",
        "Incident",
        "Integration",
        "The reporting connector stopped overnight with an expired-token message.",
        "Rotated the sandbox token and confirmed a successful synchronization.",
    ),
    (
        "Incorrect customer information",
        "Question",
        "Configuration",
        "Our demo company's primary contact and display name are outdated in the portal.",
        "The company manager updated the contact and checked the portal display.",
    ),
    (
        "Report not generating",
        "Bug",
        "Reporting",
        "The monthly activity report remains queued when a custom date range is selected.",
        "Corrected the date range and confirmed the background report job completed.",
    ),
]
ARTICLES = [
    (
        "Resetting your password",
        "Account access",
        "Open the login page and choose Forgot Password. Enter your account email and follow the reset link. In this demo, outgoing email is disabled; ask the local administrator to reset the demo user instead. Never include passwords in a ticket.",
    ),
    (
        "Updating company information",
        "Getting started",
        "Sign in with a customer manager account and review your company profile. Check the primary contact before saving changes. Ask support if an organization field is restricted.",
    ),
    (
        "Creating a support request",
        "Getting started",
        "Open My Tickets, choose New Ticket, and enter a clear subject. Describe what happened, when it started, and the impact. Include sanitized screenshots without credentials or personal data.",
    ),
    (
        "Understanding ticket priorities",
        "Getting started",
        "Low is for routine questions; Medium is for normal service requests; High is for major disruption; Urgent is for widespread service unavailability. Response targets depend on your SLA and service hours.",
    ),
    (
        "Troubleshooting login problems",
        "Account access",
        "Check the account email, browser clock, and verification code. Try a private browser window. If the issue persists, report the time and the visible error message without sharing passwords.",
    ),
    (
        "API authentication troubleshooting",
        "Integrations",
        "Check the sandbox endpoint, token expiry, and requested permissions. A 401 usually requires renewed authentication; a 403 may indicate insufficient access. Share a sanitized request ID with support, never a token.",
    ),
    (
        "Updating billing details",
        "Getting started",
        "Ask your company manager to review billing contacts and the invoice address. Quote a demo invoice reference when requesting a correction. Do not include payment-card data in a support ticket.",
    ),
    (
        "Service availability troubleshooting",
        "Integrations",
        "Check the service status and try a second network. Record the affected endpoint, first failure time, and scope. Open an Urgent ticket when all users are blocked and include sanitized diagnostics.",
    ),
    (
        "Exporting support activity",
        "Getting started",
        "Choose the relevant ticket filters and date range before exporting. Confirm that the export contains only the records you are permitted to access. Store exported files in an approved location.",
    ),
    (
        "Working with ticket replies",
        "Getting started",
        "Open a ticket to read its conversation. Reply with the requested details. Awaiting Response means support is waiting for your input. You can review the resolution and reopen a request if the problem returns.",
    ),
]


def ensure(doctype, filters, values):
    """Insert a fixture only when its stable natural key does not already exist."""
    name = frappe.db.exists(doctype, filters)
    if name:
        return frappe.get_doc(doctype, name)
    return frappe.get_doc({"doctype": doctype, **values}).insert()


def require_demo_site():
    """Refuse non-development sites, unmuted email, and non-admin execution."""
    if frappe.session.user != "Administrator":
        frappe.throw("Run the demo seeder as Administrator.")
    if not all(
        frappe.conf.get(key)
        for key in ("developer_mode", "allow_demo_seed", "mute_emails")
    ):
        frappe.throw(
            "Demo seeding requires developer_mode, allow_demo_seed and mute_emails in site_config."
        )
    if not os.environ.get("DEMO_PASSWORD"):
        frappe.throw("Set DEMO_PASSWORD in the process environment.")


def seed_people():
    """Create five agents and twenty portal users/contacts in five companies."""
    password = os.environ["DEMO_PASSWORD"]
    for handle, label, roles in AGENTS:
        email = f"{handle}@helpdesk.example.test"
        ensure(
            "User",
            email,
            {
                "email": email,
                "first_name": label,
                "user_type": "System User",
                "send_welcome_email": 0,
                "new_password": password,
                "roles": [{"role": role} for role in roles],
            },
        )
        ensure("HD Agent", {"user": email}, {"user": email, "agent_name": label})
    people = []
    for company, domain in COMPANIES:
        contacts = []
        for index in range(1, 5):
            email = f"customer{index}@{domain}.example.test"
            ensure(
                "User",
                email,
                {
                    "email": email,
                    "first_name": f"Demo {domain.title()}",
                    "last_name": f"Contact {index}",
                    "user_type": "Website User",
                    "send_welcome_email": 0,
                    "new_password": password,
                    "roles": [{"role": "HD Customer"}],
                },
            )
            contact = ensure(
                "Contact",
                {"user": email},
                {
                    "first_name": f"Demo {domain.title()}",
                    "last_name": f"Contact {index}",
                    "user": email,
                    "email_ids": [{"email_id": email, "is_primary": 1}],
                },
            )
            contacts.append({"contact_name": contact.name, "is_manager": index == 1})
            people.append((email, contact.name, company))
        ensure(
            "HD Customer",
            company,
            {
                "customer_name": company,
                "customer_type": "Company",
                "domain": f"{domain}.example.test",
                "contacts": contacts,
                "primary_contact": contacts[0]["contact_name"],
            },
        )
    return people


def seed_configuration():
    """Create native team rotations, SLA examples, and reusable replies."""
    for team, members in {
        "Demo Frontline": ["tier1", "support.admin"],
        "Demo Technical": ["tier2", "technical"],
        "Demo Escalations": ["manager", "technical"],
    }.items():
        ensure(
            "HD Team",
            team,
            {
                "team_name": team,
                "users": [
                    {"user": f"{member}@helpdesk.example.test"} for member in members
                ],
            },
        )
    today = now_datetime().date()
    holidays = ensure(
        "HD Service Holiday List",
        "Demo Service Calendar",
        {
            "holiday_list_name": "Demo Service Calendar",
            "from_date": today.replace(year=today.year - 1, month=1, day=1),
            "to_date": today.replace(year=today.year + 2, month=12, day=31),
        },
    )
    for label, condition, rank, multiplier in [
        (
            "Demo Urgent Escalation",
            "doc.priority == 'Urgent' and (doc.subject or '').startswith('[DEMO-')",
            1,
            1,
        ),
        ("Demo Standard Support", "(doc.subject or '').startswith('[DEMO-')", 2, 2),
    ]:
        ensure(
            "HD Service Level Agreement",
            label,
            {
                "service_level": label,
                "holiday_list": holidays.name,
                "condition": condition,
                "rank": rank,
                "enabled": 1,
                "apply_sla_for_resolution": 1,
                "priorities": [
                    {
                        "priority": priority,
                        "default_priority": priority == "Medium",
                        "response_time": response * multiplier,
                        "resolution_time": resolution * multiplier,
                    }
                    for priority, response, resolution in [
                        ("Low", 14400, 86400),
                        ("Medium", 7200, 28800),
                        ("High", 1800, 14400),
                        ("Urgent", 900, 7200),
                    ]
                ],
                "support_and_resolution": [
                    {"workday": day, "start_time": "08:00:00", "end_time": "17:00:00"}
                    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                ],
            },
        )
    for title, message in [
        (
            "Demo - Acknowledgement",
            "Thank you for the details. We are investigating and will update this ticket shortly.",
        ),
        (
            "Demo - Request diagnostics",
            "Please provide the approximate time, affected screen, and a sanitized error message. Do not send credentials.",
        ),
        (
            "Demo - Escalation",
            "We have moved this request to our technical escalation team. The service manager will coordinate the next update.",
        ),
        (
            "Demo - Resolution",
            "The reported issue has been corrected. Please confirm that the expected behavior is restored.",
        ),
    ]:
        ensure(
            "HD Saved Reply",
            title,
            {"title": title, "message": f"<p>{message}</p>", "scope": "Global"},
        )


def seed_knowledge_base():
    """Publish ten searchable articles using the current Article status field."""
    for title, category, content in ARTICLES:
        group = ensure(
            "HD Article Category",
            {"category_name": f"Demo - {category}"},
            {
                "category_name": f"Demo - {category}",
                "description": "Fictional evaluation guidance",
            },
        )
        ensure(
            "HD Article",
            {"title": title},
            {
                "title": title,
                "category": group.name,
                "content": f"<p>{content}</p>",
                "status": "Published",
            },
        )


def seed_ticket(index, people, anchor):
    """Create a historical conversation through native Helpdesk document methods."""
    scenario, ticket_type, category, problem, resolution = SCENARIOS[
        (index - 1) % len(SCENARIOS)
    ]
    subject = f"[DEMO-{index:03d}] {scenario}"
    if frappe.db.exists("HD Ticket", {"subject": subject}):
        return False
    email, contact, company = people[(index - 1) % len(people)]
    created = (anchor - timedelta(days=1 + index % 28)).replace(
        hour=9 + index % 5, minute=index % 60
    )
    priority = ["Low", "Medium", "High", "Urgent"][(index - 1) % 4]
    status = ["Open", "Open", "Replied", "Resolved", "Closed"][(index - 1) % 5]
    team = (
        "Demo Escalations"
        if priority == "Urgent"
        else (
            "Demo Technical"
            if category in ("Integration", "Performance", "Availability")
            else "Demo Frontline"
        )
    )
    agent = {
        "Demo Frontline": "tier1",
        "Demo Technical": "technical",
        "Demo Escalations": "manager",
    }[team]
    agent = f"{agent}@helpdesk.example.test"
    frappe.set_user(email)
    try:
        ticket = frappe.get_doc(
            {
                "doctype": "HD Ticket",
                "subject": subject,
                "description": f"<p>{problem}</p><p>Organization: {company}. This is fictional development data.</p>",
                "raised_by": email,
                "contact": contact,
                "customer": company,
                "priority": priority,
                "ticket_type": ticket_type,
                "via_customer_portal": 1,
                "creation": created,
                "opening_date": created.date(),
                "opening_time": created.time(),
                "service_level_agreement_creation": created,
            }
        ).insert(ignore_permissions=True)
        frappe.set_user("Administrator")
        ticket.reload()
        ticket.agent_group = team
        ticket.save()
        ticket.assign_agent(agent)
        ticket.add_tag("Demo", "Blue")
        ticket.add_tag(category, "Gray")
        if index % 5 != 1:
            frappe.set_user(agent)
            ticket.reply_via_agent(
                f"<p>We reproduced the reported behavior. {resolution if status in ('Resolved', 'Closed') else 'Please confirm the first affected time and whether all users are impacted.'}</p>",
                to=email,
            )
            ticket.reload()
            ticket.new_comment(
                f"<p>Internal triage: reviewed {category.lower()} diagnostics. {'Escalated to the service manager for coordination.' if priority == 'Urgent' else 'Assigned to the appropriate support queue.'}</p>"
            )
            if index % 2 == 0:
                frappe.set_user(email)
                ticket.reload()
                ticket.create_communication_via_contact(
                    "<p>Thank you. We checked with the branch team and supplied the requested details. The issue started during the morning shift.</p>"
                )
        frappe.set_user("Administrator")
        ticket.reload()
        communications = frappe.get_list(
            "Communication",
            filters={"reference_doctype": "HD Ticket", "reference_name": ticket.name},
            fields=["name", "sent_or_received"],
            order_by="creation asc",
            limit_page_length=0,
        )
        first_response = None
        last_customer_response = created
        for offset, communication in enumerate(communications):
            stamp = created + timedelta(minutes=30 * offset)
            frappe.db.set_value(
                "Communication",
                communication.name,
                {"creation": stamp, "communication_date": stamp, "modified": stamp},
                update_modified=False,
            )
            if communication.sent_or_received == "Sent":
                first_response = first_response or stamp
            else:
                last_customer_response = stamp
        ticket.first_responded_on = first_response
        ticket.last_agent_response = first_response
        ticket.last_customer_response = last_customer_response
        ticket.status = status
        if status in ("Resolved", "Closed"):
            ticket.resolution_details = f"<p>{resolution} Customer confirmed the outcome in the demo scenario.</p>"
        ticket.save()
        if status in ("Resolved", "Closed"):
            ticket.reload()
            ticket.resolution_date = created + timedelta(hours=3)
            ticket.resolution_failed_by = 0
            if sla := ticket.get_sla():
                sla.set_resolution_time(ticket)
            ticket.save()
        if status == "Replied":
            ticket.on_hold_since = created + timedelta(hours=2)
            ticket.save()
        ticket.db_set(
            {"creation": created, "modified": created + timedelta(hours=3)},
            update_modified=False,
        )
        comments = frappe.get_list(
            "Comment",
            filters={"reference_doctype": "HD Ticket", "reference_name": ticket.name},
            pluck="name",
            order_by="creation asc",
            limit_page_length=0,
        )
        for offset, name in enumerate(comments):
            stamp = created + timedelta(minutes=10 + offset * 5)
            frappe.db.set_value(
                "Comment",
                name,
                {"creation": stamp, "modified": stamp},
                update_modified=False,
            )
        frappe.db.commit()
        return True
    finally:
        frappe.set_user("Administrator")


def run():
    """Populate an explicitly opted-in development site; preserve existing fixtures."""
    require_demo_site()
    frappe.db.set_single_value(
        "System Settings",
        {"setup_complete": 1, "time_zone": "Africa/Maseru", "language": "en"},
    )
    frappe.db.set_single_value(
        "HD Settings",
        {
            "skip_email_workflow": 1,
            "send_acknowledgement_email": 0,
            "enable_reply_email_to_agent": 0,
            "enable_reply_email_via_agent": 0,
            "enable_email_ticket_feedback": 0,
            "setup_complete": 1,
            "initial_helpdesk_name_setup_skipped": 1,
            "persona_captured": 1,
        },
    )
    people = seed_people()
    seed_configuration()
    seed_knowledge_base()
    frappe.db.commit()
    anchor = now_datetime()
    created = sum(seed_ticket(index, people, anchor) for index in range(1, 51))
    frappe.clear_cache()
    frappe.db.commit()
    result = {
        "created_tickets": created,
        "demo_tickets": frappe.db.count("HD Ticket", {"subject": ["like", "[DEMO-%"]}),
        "agents": 5,
        "customer_contacts": 20,
        "companies": 5,
        "articles": 10,
    }
    print(frappe.as_json(result))
    return result
