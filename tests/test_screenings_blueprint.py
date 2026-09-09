from app.extensions import db
from app.models.program import ProgramState
from app.models.screening import ScreeningState
from app.services.program_service import program_service
from app.services.screening_service import screening_service


def _log_in(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id


def _program_payload(name="Screening Test Program"):
    return {
        "name": name,
        "description": "Program used for screening endpoint tests",
        "startDate": "2026-01-01",
        "endDate": "2026-12-31",
    }


def _screening_payload(**overrides):
    payload = {
        "filmTitle": "Interstellar",
        "filmCast": "Matthew McConaughey Anne Hathaway",
        "filmGenres": "Science Fiction",
        "filmDurationMinutes": 169,
        "auditoriumName": "Auditorium A",
        "startTime": "2026-05-10T18:00:00",
    }

    payload.update(overrides)
    return payload


def _create_program(client, programmer, name="Screening Test Program"):
    _log_in(client, programmer)

    response = client.post(
        "/programs",
        json=_program_payload(name),
    )

    assert response.status_code == 201

    return response.get_json()


def _create_screening(client, program_id, submitter, **overrides):
    _log_in(client, submitter)

    response = client.post(
        f"/programs/{program_id}/screenings",
        json=_screening_payload(**overrides),
    )

    assert response.status_code == 201

    return response.get_json()


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------


def test_create_screening_success(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    response = client.post(
        f"/programs/{program['id']}/screenings",
        json=_screening_payload(),
    )

    # Είμαστε ακόμη logged-in ως programmer,
    # άρα αλλάζουμε στον submitter.
    _log_in(client, submitter)

    response = client.post(
        f"/programs/{program['id']}/screenings",
        json=_screening_payload(),
    )

    assert response.status_code == 201

    body = response.get_json()

    assert body["filmTitle"] == "Interstellar"
    assert body["state"] == "CREATED"
    assert body["submitterId"] == submitter.id


def test_create_screening_requires_authentication(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")

    program = _create_program(
        client,
        programmer,
    )

    with client.session_transaction() as sess:
        sess.clear()

    response = client.post(
        f"/programs/{program['id']}/screenings",
        json=_screening_payload(),
    )

    assert response.status_code == 401


def test_create_screening_missing_title_returns_400(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    _log_in(client, submitter)

    response = client.post(
        f"/programs/{program['id']}/screenings",
        json={"filmTitle": ""},
    )

    assert response.status_code == 400


def test_create_screening_rejects_programmer(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")

    program = _create_program(
        client,
        programmer,
    )

    response = client.post(
        f"/programs/{program['id']}/screenings",
        json=_screening_payload(),
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET / SEARCH
# ---------------------------------------------------------------------------


def test_get_screening_success(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    response = client.get(
        f"/programs/{program['id']}/screenings/{screening['id']}"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["id"] == screening["id"]
    assert body["filmTitle"] == "Interstellar"


def test_get_screening_not_found_returns_404(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")

    program = _create_program(
        client,
        programmer,
    )

    response = client.get(
        f"/programs/{program['id']}/screenings/does-not-exist"
    )

    assert response.status_code == 404


def test_search_screenings_success(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    _create_screening(
        client,
        program["id"],
        submitter,
        filmTitle="Star Wars",
    )

    response = client.get(
        f"/programs/{program['id']}/screenings",
        query_string={
            "filmTitle": "star war",
        },
    )

    assert response.status_code == 200

    results = response.get_json()["results"]

    assert len(results) == 1
    assert results[0]["filmTitle"] == "Star Wars"


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------


def test_update_screening_success(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    response = client.put(
        f"/programs/{program['id']}/screenings/{screening['id']}",
        json={
            "filmTitle": "Updated Film",
            "auditoriumName": "Auditorium B",
        },
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["filmTitle"] == "Updated Film"
    assert body["auditoriumName"] == "Auditorium B"


def test_update_screening_forbidden_for_outsider(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")
    outsider = user_factory(username="outsider")

    program = _create_program(
        client,
        programmer,
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    _log_in(client, outsider)

    response = client.put(
        f"/programs/{program['id']}/screenings/{screening['id']}",
        json={
            "filmTitle": "Illegal Update",
        },
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# SUBMIT / WITHDRAW
# ---------------------------------------------------------------------------


def test_submit_screening_success(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    client.post(
        f"/programs/{program['id']}/transitions",
        json={
            "targetState": "SUBMISSION",
        },
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    response = client.post(
        f"/programs/{program['id']}/screenings/{screening['id']}/submit"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["state"] == "SUBMITTED"
    assert body["endTime"] is not None


def test_submit_screening_wrong_state_returns_409(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    response = client.post(
        f"/programs/{program['id']}/screenings/{screening['id']}/submit"
    )

    assert response.status_code == 409


def test_withdraw_screening_success(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    response = client.delete(
        f"/programs/{program['id']}/screenings/{screening['id']}"
    )

    assert response.status_code == 204


# ---------------------------------------------------------------------------
# HANDLER
# ---------------------------------------------------------------------------


def test_assign_handler_success(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")
    staff = user_factory(username="staff")

    program = _create_program(
        client,
        programmer,
    )

    client.post(
        f"/programs/{program['id']}/roles",
        json={
            "userId": staff.id,
            "roleType": "STAFF",
        },
    )

    client.post(
        f"/programs/{program['id']}/transitions",
        json={
            "targetState": "SUBMISSION",
        },
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    client.post(
        f"/programs/{program['id']}/screenings/{screening['id']}/submit"
    )

    _log_in(client, programmer)

    client.post(
        f"/programs/{program['id']}/transitions",
        json={
            "targetState": "ASSIGNMENT",
        },
    )

    response = client.post(
        f"/programs/{program['id']}/screenings/{screening['id']}/handler",
        json={
            "userId": staff.id,
        },
    )

    assert response.status_code == 200
    assert response.get_json()["handlerId"] == staff.id


def test_assign_handler_missing_user_id_returns_400(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    _log_in(client, programmer)

    response = client.post(
        f"/programs/{program['id']}/screenings/{screening['id']}/handler",
        json={},
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# REVIEW
# ---------------------------------------------------------------------------


def test_review_screening_success(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")
    staff = user_factory(username="staff")

    program = _create_program(
        client,
        programmer,
    )

    client.post(
        f"/programs/{program['id']}/roles",
        json={
            "userId": staff.id,
            "roleType": "STAFF",
        },
    )

    client.post(
        f"/programs/{program['id']}/transitions",
        json={
            "targetState": "SUBMISSION",
        },
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    client.post(
        f"/programs/{program['id']}/screenings/{screening['id']}/submit"
    )

    _log_in(client, programmer)

    client.post(
        f"/programs/{program['id']}/transitions",
        json={
            "targetState": "ASSIGNMENT",
        },
    )

    client.post(
        f"/programs/{program['id']}/screenings/{screening['id']}/handler",
        json={
            "userId": staff.id,
        },
    )

    client.post(
        f"/programs/{program['id']}/transitions",
        json={
            "targetState": "REVIEW",
        },
    )

    _log_in(client, staff)

    response = client.post(
        f"/programs/{program['id']}/screenings/{screening['id']}/review",
        json={
            "score": 8.5,
            "comments": "Very good screening",
        },
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["state"] == "REVIEWED"
    assert body["reviewScore"] == 8.5


# ---------------------------------------------------------------------------
# APPROVE / REJECT
# ---------------------------------------------------------------------------


def test_approve_screening_success(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    screening_obj = db.session.get(
        __import__(
            "app.models.screening",
            fromlist=["Screening"],
        ).Screening,
        screening["id"],
    )

    screening_obj.state = ScreeningState.REVIEWED

    program_obj = screening_obj.program
    program_obj.state = ProgramState.SCHEDULING

    db.session.commit()

    _log_in(client, programmer)

    response = client.post(
        f"/programs/{program['id']}/screenings/{screening['id']}/approve",
        json={
            "notes": "Approved with minor changes",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["state"] == "APPROVED"


def test_reject_screening_success(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    screening_obj = db.session.get(
        __import__(
            "app.models.screening",
            fromlist=["Screening"],
        ).Screening,
        screening["id"],
    )

    screening_obj.state = ScreeningState.REVIEWED
    screening_obj.program.state = ProgramState.SCHEDULING

    db.session.commit()

    _log_in(client, programmer)

    response = client.post(
        f"/programs/{program['id']}/screenings/{screening['id']}/reject",
        json={
            "reason": "Does not fit the program",
        },
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["state"] == "REJECTED"
    assert body["rejectionReason"] == "Does not fit the program"


# ---------------------------------------------------------------------------
# FINAL SUBMIT / ACCEPT
# ---------------------------------------------------------------------------


def test_final_submit_screening_success(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    screening_obj = db.session.get(
        __import__(
            "app.models.screening",
            fromlist=["Screening"],
        ).Screening,
        screening["id"],
    )

    screening_obj.state = ScreeningState.APPROVED
    screening_obj.program.state = ProgramState.FINAL_SUBMISSION

    db.session.commit()

    _log_in(client, submitter)

    response = client.post(
        f"/programs/{program['id']}/screenings/{screening['id']}/final-submit",
        json={
            "auditoriumName": "Final Auditorium",
        },
    )

    assert response.status_code == 200


def test_accept_screening_success(
    db,
    client,
    user_factory,
):
    programmer = user_factory(username="programmer")
    submitter = user_factory(username="submitter")

    program = _create_program(
        client,
        programmer,
    )

    screening = _create_screening(
        client,
        program["id"],
        submitter,
    )

    screening_obj = db.session.get(
        __import__(
            "app.models.screening",
            fromlist=["Screening"],
        ).Screening,
        screening["id"],
    )

    screening_obj.state = ScreeningState.APPROVED
    screening_obj.final_submitted = True
    screening_obj.program.state = ProgramState.DECISION

    db.session.commit()

    _log_in(client, programmer)

    response = client.post(
        f"/programs/{program['id']}/screenings/{screening['id']}/accept"
    )

    assert response.status_code == 200
    assert response.get_json()["state"] == "SCHEDULED"