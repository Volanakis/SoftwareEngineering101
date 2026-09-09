"""End-to-end integration pass across BOTH modules (Program + Screening) over HTTP.

Complements test_screening_workflow.py (single happy path) by driving one program
with three screenings to three different terminal outcomes in a single run:

    * screening A -> SCHEDULED        (reviewed, approved, final-submitted, accepted)
    * screening B -> REJECTED         (manual rejection by PROGRAMMER at SCHEDULING)
    * screening C -> REJECTED         (automatic rejection on entering DECISION,
                                       approved but never final-submitted)

Also checks the ΜΛΑ-5 audit trail and the visitor-facing redaction of the
announced program.
"""

import logging

import pytest

from app.extensions import db
from app.models.screening import Screening, ScreeningState


def _login(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id


def _logout(client):
    with client.session_transaction() as sess:
        sess.clear()


def _transition(client, pid, target):
    resp = client.post(f"/programs/{pid}/transitions", json={"targetState": target})
    assert resp.status_code == 200, (target, resp.get_json())


def _new_screening(client, pid, submitter, title):
    _login(client, submitter)
    resp = client.post(
        f"/programs/{pid}/screenings",
        json={
            "filmTitle": title,
            "filmCast": "Some Cast",
            "filmGenres": "Drama",
            "filmDurationMinutes": 120,
            "auditoriumName": "Hall 1",
            "startTime": "2026-06-01T20:00:00",
        },
    )
    assert resp.status_code == 201, resp.get_json()
    sid = resp.get_json()["id"]
    resp = client.post(f"/programs/{pid}/screenings/{sid}/submit")
    assert resp.status_code == 200, resp.get_json()
    return sid


@pytest.mark.usefixtures("db")
def test_full_program_and_screening_lifecycle(client, user_factory, caplog):
    caplog.set_level(logging.INFO, logger="app.services")

    programmer = user_factory(username="int-programmer")
    staff = user_factory(username="int-staff")
    submitter_a = user_factory(username="int-sub-a")
    submitter_b = user_factory(username="int-sub-b")
    submitter_c = user_factory(username="int-sub-c")

    # --- program setup -------------------------------------------------------
    _login(client, programmer)
    resp = client.post(
        "/programs",
        json={
            "name": "Integration Season",
            "description": "multi-outcome integration test",
            "startDate": "2026-01-01",
            "endDate": "2026-12-31",
        },
    )
    assert resp.status_code == 201
    pid = resp.get_json()["id"]

    resp = client.post(
        f"/programs/{pid}/roles",
        json={"userId": staff.id, "roleType": "STAFF"},
    )
    assert resp.status_code == 200

    # --- SUBMISSION: three screenings submitted ---------------------------
    _login(client, programmer)
    _transition(client, pid, "SUBMISSION")

    sa = _new_screening(client, pid, submitter_a, "Alpha Film")
    sb = _new_screening(client, pid, submitter_b, "Beta Film")
    sc = _new_screening(client, pid, submitter_c, "Gamma Film")

    # --- ASSIGNMENT: one handler each --------------------------------------
    _login(client, programmer)
    _transition(client, pid, "ASSIGNMENT")
    for sid in (sa, sb, sc):
        resp = client.post(
            f"/programs/{pid}/screenings/{sid}/handler",
            json={"userId": staff.id},
        )
        assert resp.status_code == 200, resp.get_json()

    # --- REVIEW ----------------------------------------------------------
    _transition(client, pid, "REVIEW")
    _login(client, staff)
    for sid, score in ((sa, 9), (sb, 4), (sc, 8)):
        resp = client.post(
            f"/programs/{pid}/screenings/{sid}/review",
            json={"score": score, "comments": f"review of {sid}"},
        )
        assert resp.status_code == 200, resp.get_json()

    # --- SCHEDULING: approve A & C, manually reject B --------------------
    _login(client, programmer)
    _transition(client, pid, "SCHEDULING")

    assert client.post(f"/programs/{pid}/screenings/{sa}/approve", json={}).status_code == 200
    assert client.post(f"/programs/{pid}/screenings/{sc}/approve", json={}).status_code == 200

    resp = client.post(
        f"/programs/{pid}/screenings/{sb}/reject",
        json={"reason": "score below bar"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["state"] == "REJECTED"
    assert resp.get_json()["rejectionReason"] == "score below bar"

    # --- FINAL_SUBMISSION: A submits final, C does not -----------------
    _transition(client, pid, "FINAL_SUBMISSION")
    _login(client, submitter_a)
    resp = client.post(
        f"/programs/{pid}/screenings/{sa}/final-submit",
        json={"auditoriumName": "Hall 2 (final)"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["finalSubmitted"] is True

    # --- DECISION: C auto-rejected, A accepted -> SCHEDULED -----------
    _login(client, programmer)
    _transition(client, pid, "DECISION")

    resp = client.post(f"/programs/{pid}/screenings/{sa}/accept")
    assert resp.status_code == 200
    assert resp.get_json()["state"] == "SCHEDULED"

    _transition(client, pid, "ANNOUNCED")

    # --- final states ------------------------------------------------
    states = {
        s.id: s.state
        for s in Screening.query.filter_by(program_id=pid).all()
    }
    assert states[sa] == ScreeningState.SCHEDULED
    assert states[sb] == ScreeningState.REJECTED
    assert states[sc] == ScreeningState.REJECTED

    sc_obj = db.session.get(Screening, sc)
    assert sc_obj.rejection_reason  # ΛΑ-3.8.3: reason recorded even for auto-reject
    assert "final submission" in sc_obj.rejection_reason.lower()

    # --- visitor view: program redacted, only SCHEDULED screening public ---
    _logout(client)

    resp = client.get(f"/programs/{pid}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["state"] == "ANNOUNCED"
    assert "programmers" not in body and "staff" not in body and "creationDate" not in body

    resp = client.get(f"/programs/{pid}/screenings")
    assert resp.status_code == 200
    results = resp.get_json()["results"]
    assert [r["id"] for r in results] == [sa]
    assert "submitterId" not in results[0] and "reviewScore" not in results[0]

    # --- ΜΛΑ-5 audit trail --------------------------------------------
    messages = "\n".join(r.getMessage() for r in caplog.records)
    assert "Program created" in messages
    assert "Program state changed" in messages and "to=ANNOUNCED" in messages
    assert "Screening submitted" in messages
    assert "Screening auto-rejected" in messages
    assert "Handler assigned" in messages
