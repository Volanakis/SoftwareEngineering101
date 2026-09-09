from app.extensions import db
from app.models.program import ProgramState
from app.models.screening import Screening, ScreeningState


def _log_in(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id


def _program_payload():
    return {
        "name": "Full Workflow Program",
        "description": "Integration workflow test",
        "startDate": "2026-01-01",
        "endDate": "2026-12-31",
    }


def _screening_payload():
    return {
        "filmTitle": "Workflow Film",
        "filmCast": "Actor One Actor Two",
        "filmGenres": "Drama",
        "filmDurationMinutes": 120,
        "auditoriumName": "Auditorium A",
        "startTime": "2026-05-10T18:00:00",
    }


def test_full_screening_workflow(
    db,
    client,
    user_factory,
):
    programmer = user_factory(
        username="workflow-programmer"
    )

    submitter = user_factory(
        username="workflow-submitter"
    )

    staff = user_factory(
        username="workflow-staff"
    )

    # --------------------------------------------------
    # 1. Create program
    # --------------------------------------------------

    _log_in(client, programmer)

    response = client.post(
        "/programs",
        json=_program_payload(),
    )

    assert response.status_code == 201

    program = response.get_json()
    program_id = program["id"]

    # --------------------------------------------------
    # 2. Add STAFF
    # --------------------------------------------------

    response = client.post(
        f"/programs/{program_id}/roles",
        json={
            "userId": staff.id,
            "roleType": "STAFF",
        },
    )

    assert response.status_code == 200

    # --------------------------------------------------
    # 3. CREATED -> SUBMISSION
    # --------------------------------------------------

    response = client.post(
        f"/programs/{program_id}/transitions",
        json={
            "targetState": "SUBMISSION",
        },
    )

    assert response.status_code == 200

    # --------------------------------------------------
    # 4. Create screening
    # --------------------------------------------------

    _log_in(client, submitter)

    response = client.post(
        f"/programs/{program_id}/screenings",
        json=_screening_payload(),
    )

    assert response.status_code == 201

    screening = response.get_json()
    screening_id = screening["id"]

    assert screening["state"] == "CREATED"

    # --------------------------------------------------
    # 5. Submit screening
    # --------------------------------------------------

    response = client.post(
        f"/programs/{program_id}/screenings/{screening_id}/submit"
    )

    assert response.status_code == 200

    screening = response.get_json()

    assert screening["state"] == "SUBMITTED"
    assert screening["endTime"] is not None

    # --------------------------------------------------
    # 6. SUBMISSION -> ASSIGNMENT
    # --------------------------------------------------

    _log_in(client, programmer)

    response = client.post(
        f"/programs/{program_id}/transitions",
        json={
            "targetState": "ASSIGNMENT",
        },
    )

    assert response.status_code == 200

    # --------------------------------------------------
    # 7. Assign STAFF handler
    # --------------------------------------------------

    response = client.post(
        f"/programs/{program_id}/screenings/{screening_id}/handler",
        json={
            "userId": staff.id,
        },
    )

    assert response.status_code == 200

    screening = response.get_json()

    assert screening["handlerId"] == staff.id

    # --------------------------------------------------
    # 8. ASSIGNMENT -> REVIEW
    # --------------------------------------------------

    response = client.post(
        f"/programs/{program_id}/transitions",
        json={
            "targetState": "REVIEW",
        },
    )

    assert response.status_code == 200

    # --------------------------------------------------
    # 9. Review screening
    # --------------------------------------------------

    _log_in(client, staff)

    response = client.post(
        f"/programs/{program_id}/screenings/{screening_id}/review",
        json={
            "score": 9.0,
            "comments": "Excellent screening",
        },
    )

    assert response.status_code == 200

    screening = response.get_json()

    assert screening["state"] == "REVIEWED"
    assert screening["reviewScore"] == 9.0

    # --------------------------------------------------
    # 10. REVIEW -> SCHEDULING
    # --------------------------------------------------

    _log_in(client, programmer)

    response = client.post(
        f"/programs/{program_id}/transitions",
        json={
            "targetState": "SCHEDULING",
        },
    )

    assert response.status_code == 200

    # --------------------------------------------------
    # 11. Approve screening
    # --------------------------------------------------

    response = client.post(
        f"/programs/{program_id}/screenings/{screening_id}/approve",
        json={
            "notes": "Approved",
        },
    )

    assert response.status_code == 200

    screening = response.get_json()

    assert screening["state"] == "APPROVED"

    # --------------------------------------------------
    # 12. SCHEDULING -> FINAL_SUBMISSION
    # --------------------------------------------------

    response = client.post(
        f"/programs/{program_id}/transitions",
        json={
            "targetState": "FINAL_SUBMISSION",
        },
    )

    assert response.status_code == 200

    # --------------------------------------------------
    # 13. Final submit
    # --------------------------------------------------

    _log_in(client, submitter)

    response = client.post(
        f"/programs/{program_id}/screenings/{screening_id}/final-submit",
        json={
            "auditoriumName": "Auditorium Final",
        },
    )

    assert response.status_code == 200

    # --------------------------------------------------
    # 14. FINAL_SUBMISSION -> DECISION
    # --------------------------------------------------

    _log_in(client, programmer)

    response = client.post(
        f"/programs/{program_id}/transitions",
        json={
            "targetState": "DECISION",
        },
    )

    assert response.status_code == 200

    # Verify it was NOT auto-rejected
    screening_obj = db.session.get(
        Screening,
        screening_id,
    )

    assert (
        screening_obj.state
        == ScreeningState.APPROVED
    )

    assert screening_obj.final_submitted is True

    # --------------------------------------------------
    # 15. Accept screening
    # --------------------------------------------------

    response = client.post(
        f"/programs/{program_id}/screenings/{screening_id}/accept"
    )

    assert response.status_code == 200

    screening = response.get_json()

    assert screening["state"] == "SCHEDULED"

    # --------------------------------------------------
    # 16. DECISION -> ANNOUNCED
    # --------------------------------------------------

    response = client.post(
        f"/programs/{program_id}/transitions",
        json={
            "targetState": "ANNOUNCED",
        },
    )

    assert response.status_code == 200

    # --------------------------------------------------
    # 17. Visitor can now view public screening
    # --------------------------------------------------

    with client.session_transaction() as sess:
        sess.clear()

    response = client.get(
        f"/programs/{program_id}/screenings/{screening_id}"
    )

    assert response.status_code == 200

    public_screening = response.get_json()

    assert public_screening["filmTitle"] == "Workflow Film"
    assert public_screening["state"] == "SCHEDULED"
    assert public_screening["auditoriumName"] == "Auditorium Final"

    # Sensitive fields must be hidden
    assert "submitterId" not in public_screening
    assert "handlerId" not in public_screening
    assert "reviewScore" not in public_screening
    assert "reviewComments" not in public_screening

    # --------------------------------------------------
    # 18. Visitor search also sees it
    # --------------------------------------------------

    response = client.get(
        f"/programs/{program_id}/screenings"
    )

    assert response.status_code == 200

    results = response.get_json()["results"]

    assert len(results) == 1
    assert results[0]["id"] == screening_id