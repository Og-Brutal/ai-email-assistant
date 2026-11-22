from fastapi.testclient import TestClient

from app.gmail.deps import get_gmail
from app.gmail.schemas import EmailPage, EmailSummary, Label, ParsedEmail, Thread
from app.main import app
from app.security.session import current_user


class FakeGmail:
    def list_emails(self, query="", max_results=20, page_token=None, label_ids=None):
        self.last_query = query
        return EmailPage(
            emails=[EmailSummary(id="m1", thread_id="t1", **{"from": "a@x.com"}, subject="Hi", unread=True)],
            next_page_token=None,
        )

    def get_email(self, message_id):
        return ParsedEmail(id=message_id, **{"from": "a@x.com"}, subject="Hi", body_clean="Hello")

    def get_thread(self, thread_id):
        return Thread(id=thread_id, messages=[self.get_email("m1")])

    def list_labels(self):
        return [Label(id="INBOX", name="INBOX", type="system")]


def _client_with_fake() -> TestClient:
    app.dependency_overrides[get_gmail] = lambda: FakeGmail()
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_emails_need_login():
    assert TestClient(app).get("/emails").status_code == 401


def test_gmail_not_connected_when_no_token():
    app.dependency_overrides[current_user] = lambda: "owner@example.com"
    r = TestClient(app).get("/emails")
    assert r.status_code == 401
    assert r.json()["detail"] == "gmail_not_connected"


def test_list_emails_uses_from_alias():
    r = _client_with_fake().get("/emails?q=is:unread")
    assert r.status_code == 200
    body = r.json()
    assert body["emails"][0]["from"] == "a@x.com"
    assert body["emails"][0]["unread"] is True


def test_get_email_and_thread():
    c = _client_with_fake()
    assert c.get("/emails/m1").json()["body_clean"] == "Hello"
    assert len(c.get("/threads/t1").json()["messages"]) == 1


def test_invalid_id_rejected():
    assert _client_with_fake().get("/emails/..%2F..%2Fetc").status_code in (404, 422)


def test_page_size_limit():
    assert _client_with_fake().get("/emails?max_results=500").status_code == 422
