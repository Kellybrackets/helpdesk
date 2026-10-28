"""Exercise real local API flows with separate admin, agent, and customer sessions."""

import http.cookiejar
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
CONFIG = dict(
    line.split("=", 1)
    for line in ROOT.joinpath(".env").read_text().splitlines()
    if line and not line.startswith("#")
)
BASE = f"http://127.0.0.1:{CONFIG.get('HTTP_PORT', '8300')}"
TICKET_API = "helpdesk.helpdesk.doctype.hd_ticket.api"


class Session:
    def __init__(self, username=None, password=None):
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        self.csrf = None
        if username:
            self.call("login", usr=username, pwd=password)
            boot = self.call("helpdesk.www.helpdesk.index.get_context_for_dev")
            self.csrf = boot["csrf_token"]
            assert boot["session_user"] == username

    def request(self, path, data=None, method=None, raw=False):
        headers = {"Host": "helpdesk.localhost", "Content-Type": "application/json"}
        if self.csrf:
            headers["X-Frappe-CSRF-Token"] = self.csrf
        request = urllib.request.Request(
            BASE + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers=headers,
            method=method,
        )
        try:
            with self.opener.open(request, timeout=60) as response:
                body = response.read().decode()
                return body if raw else json.loads(body)
        except urllib.error.HTTPError as error:
            body = error.read().decode()
            try:
                detail = json.loads(body).get("exception", "Request failed")
            except json.JSONDecodeError:
                detail = "Non-JSON error response"
            raise AssertionError(
                f"HTTP {error.code} at {path.split('?')[0]}: {detail}"
            ) from None

    def call(self, rpc_method, **arguments):
        return self.request("/api/method/" + rpc_method, arguments).get("message")

    def documents(self, doctype, filters=None, fields=None):
        query = urllib.parse.urlencode(
            {
                "filters": json.dumps(filters or {}),
                "fields": json.dumps(fields or ["name"]),
                "limit_page_length": 100,
            }
        )
        return self.request(
            "/api/resource/" + urllib.parse.quote(doctype) + "?" + query
        )["data"]

    def ticket(self, name, **values):
        return self.request(
            "/api/resource/HD%20Ticket/" + urllib.parse.quote(str(name)),
            values or None,
            "PUT" if values else "GET",
        )["data"]

    def ticket_method(self, name, method, **arguments):
        return self.call(
            "run_doc_method", dt="HD Ticket", dn=name, method=method, args=arguments
        )


def main():
    admin = Session("Administrator", CONFIG["ADMIN_PASSWORD"])
    print("PASS Administrator login")
    demos = admin.documents(
        "HD Ticket",
        {"subject": ["like", "[DEMO-%"]},
        ["name", "subject", "status", "priority"],
    )
    assert len(demos) == 50, f"Expected 50 demo tickets, found {len(demos)}"
    assert {row["status"] for row in demos} == {"Open", "Replied", "Resolved", "Closed"}
    assert {row["priority"] for row in demos} == {"Low", "Medium", "High", "Urgent"}
    assert (
        len(admin.documents("HD Agent", {"user": ["like", "%@helpdesk.example.test"]}))
        == 5
    )
    assert (
        len(admin.documents("User", {"email": ["like", "customer%@%.example.test"]}))
        == 20
    )
    print("PASS demo counts, priorities and native statuses")
    agent = Session("tier1@helpdesk.example.test", CONFIG["DEMO_PASSWORD"])
    assert agent.documents("HD Ticket", {"subject": ["like", "[DEMO-%"]})
    detail = agent.call(TICKET_API + ".get_one", name=demos[0]["name"])
    assert detail["subject"].startswith("[DEMO-")
    html = agent.request("/helpdesk/tickets", raw=True)
    assert 'id="app"' in html
    assets = re.findall(r'(?:src|href)="(/assets/[^" ]+\.(?:js|css))"', html)
    assert assets, "Missing compiled frontend assets"
    for asset in assets:
        agent.request(asset, raw=True)
    print("PASS agent ticket list/detail API, SPA HTML and built assets")
    customer = Session("customer2@cedar.example.test", CONFIG["DEMO_PASSWORD"])
    customer_html = customer.request("/helpdesk/my-tickets", raw=True)
    assert 'id="app"' in customer_html
    created = customer.call(
        TICKET_API + ".new",
        doc={
            "subject": f"[VERIFY] Portal workflow {uuid4().hex[:8]}",
            "description": "<p>Fictional customer request created by the development verification script.</p>",
        },
    )
    name = created["name"]
    assert (
        customer.call(TICKET_API + ".get_one", name=name)["raised_by"]
        == "customer2@cedar.example.test"
    )
    admin.ticket(name, agent_group="Demo Frontline", priority="High")
    agent.call(
        "frappe.desk.form.assign_to.add",
        doctype="HD Ticket",
        name=name,
        assign_to=["tier1@helpdesk.example.test"],
    )
    assert "tier1@helpdesk.example.test" in {
        row["name"]
        for row in agent.call(TICKET_API + ".get_ticket_assignees", ticket=name)
    }
    agent.ticket_method(
        name,
        "reply_via_agent",
        message="<p>Verification agent reply: we are investigating.</p>",
        to="customer2@cedar.example.test",
    )
    agent.ticket_method(
        name,
        "new_comment",
        content="<p>Verification internal note; visible only to support agents.</p>",
    )
    detail = agent.call(TICKET_API + ".get_one", name=name)
    assert any(
        "Verification agent reply" in (row.get("content") or "")
        for row in detail["communications"]
    )
    assert detail["comments"], "Internal comment was not persisted"
    agent.ticket(name, status="Replied")
    assert admin.ticket(name)["status"] == "Replied"
    customer.ticket_method(
        name,
        "create_communication_via_contact",
        message="<p>Verification customer reply: here are the requested details.</p>",
    )
    assert admin.ticket(name)["status"] == "Open"
    customer_detail = customer.call(
        TICKET_API + ".get_one", name=name, is_customer_portal=True
    )
    assert not customer_detail[
        "comments"
    ], "Customer received private internal comments"
    assert any(
        "Verification customer reply" in (row.get("content") or "")
        for row in customer_detail["communications"]
    )
    agent.ticket(
        name,
        status="Resolved",
        resolution_details="<p>Verified local evaluation workflow.</p>",
    )
    assert admin.ticket(name)["status"] == "Resolved"
    print(
        f"PASS customer creation, assignment, agent/customer replies, private comment and status transitions (ticket {name})"
    )
    stranger = Session("customer2@copper.example.test", CONFIG["DEMO_PASSWORD"])
    try:
        stranger.call(TICKET_API + ".get_one", name=name, is_customer_portal=True)
    except AssertionError as error:
        assert "403" in str(error) or "PermissionError" in str(error), str(error)
    else:
        raise AssertionError("Unrelated customer accessed the verification ticket")
    print("PASS customer isolation")
    articles = admin.documents("HD Article", {"status": "Published"}, ["name", "title"])
    expected = {
        "Resetting your password",
        "API authentication troubleshooting",
        "Working with ticket replies",
    }
    assert len(articles) >= 10 and expected.issubset({row["title"] for row in articles})
    guest = Session()
    for article in articles:
        assert (
            guest.call("helpdesk.api.knowledge_base.get_article", name=article["name"])[
                "status"
            ]
            == "Published"
        )
    assert 'id="app"' in guest.request("/helpdesk/kb-public", raw=True)
    print("PASS public knowledge-base articles and customer portal HTML")
    print(
        "HTTP verification passed. Browser rendering and seed rerun checks are separate."
    )


if __name__ == "__main__":
    main()
