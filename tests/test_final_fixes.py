from app.extensions import db as sqlalchemy_db
from app.models.program import Program, ProgramRole, ProgramState
from app.models.screening import Screening, ScreeningState


def _program_payload(name="Final Fixes Program", **overrides):
    payload = {
        "name": name,
        "description": "Regression test program",
        "startDate": "2026-10-01",
        "endDate": "2026-10-31",
    }
    payload.update(overrides)
    return payload


def _login(client, user, password="password123"):
    return client.post(
        "/auth/login",
        json={"username": user.username, "password": password},
    )


def _create_program(client, programmer, name="Final Fixes Program"):
    assert _login(client, programmer).status_code == 200
    response = client.post("/programs", json=_program_payload(name))
    assert response.status_code == 201
    return response.get_json()


def test_login_and_logout_endpoints(db, client, user_factory):
    user = user_factory(username="login-user", password="correct-password")

    response = _login(client, user, "correct-password")
    assert response.status_code == 200
    assert response.get_json()["username"] == "login-user"

    assert client.post("/programs", json=_program_payload()).status_code == 201
    assert client.post("/auth/logout").status_code == 204
    assert client.post("/programs", json=_program_payload("After Logout")).status_code == 401


def test_login_validation_and_json_errors_are_consistent(db, client, user_factory):
    user_factory(username="login-user", password="correct-password")

    missing = client.post("/auth/login", json={"username": "login-user"})
    wrong = client.post(
        "/auth/login",
        json={"username": "login-user", "password": "wrong"},
    )
    unknown = client.get("/does-not-exist")

    assert missing.status_code == 400
    assert wrong.status_code == 401
    assert unknown.status_code == 404
    assert unknown.is_json
    assert "error" in unknown.get_json()


def test_program_dates_are_validated_without_500(db, client, user_factory):
    programmer = user_factory(username="date-programmer")
    assert _login(client, programmer).status_code == 200

    reversed_dates = client.post(
        "/programs",
        json=_program_payload(
            "Reversed", startDate="2026-12-31", endDate="2026-01-01"
        ),
    )
    wrong_type = client.post(
        "/programs",
        json=_program_payload("Wrong Type", startDate=123),
    )
    array_body = client.post("/programs", json=["not", "an", "object"])

    assert reversed_dates.status_code == 400
    assert wrong_type.status_code == 400
    assert array_body.status_code == 400


def test_private_program_is_hidden_until_announced(db, client, user_factory):
    programmer = user_factory(username="visibility-programmer")
    program = _create_program(client, programmer)
    assert client.post("/auth/logout").status_code == 204

    assert client.get(f"/programs/{program['id']}").status_code == 404
    assert client.get("/programs").get_json()["results"] == []

    stored = sqlalchemy_db.session.get(Program, program["id"])
    stored.state = ProgramState.ANNOUNCED
    sqlalchemy_db.session.commit()

    public_program = client.get(f"/programs/{program['id']}")
    assert public_program.status_code == 200
    assert public_program.get_json()["programmerNames"] == [programmer.full_name]
    assert len(client.get("/programs").get_json()["results"]) == 1


def test_program_search_filters_by_screening_fields(db, client, user_factory):
    programmer = user_factory(username="filter-programmer")
    submitter = user_factory(username="filter-submitter")
    program = _create_program(client, programmer)

    assert _login(client, submitter).status_code == 200
    response = client.post(
        f"/programs/{program['id']}/screenings",
        json={"filmTitle": "Hidden Galaxy", "auditoriumName": "Blue Hall"},
    )
    assert response.status_code == 201

    assert _login(client, programmer).status_code == 200
    title_results = client.get(
        "/programs", query_string={"filmTitle": "galaxy"}
    ).get_json()["results"]
    hall_results = client.get(
        "/programs", query_string={"auditorium": "blue"}
    ).get_json()["results"]
    missing_results = client.get(
        "/programs", query_string={"filmTitle": "no such film"}
    ).get_json()["results"]

    assert [item["id"] for item in title_results] == [program["id"]]
    assert [item["id"] for item in hall_results] == [program["id"]]
    assert missing_results == []


def test_role_removal_preserves_creator(db, client, user_factory):
    creator = user_factory(username="role-creator")
    added_programmer = user_factory(username="role-programmer")
    staff = user_factory(username="role-staff")
    program = _create_program(client, creator)

    for user, role in ((added_programmer, "PROGRAMMER"), (staff, "STAFF")):
        response = client.post(
            f"/programs/{program['id']}/roles",
            json={"userId": user.id, "roleType": role},
        )
        assert response.status_code == 200

    assert client.delete(
        f"/programs/{program['id']}/roles/{added_programmer.id}"
    ).status_code == 204
    assert client.delete(
        f"/programs/{program['id']}/roles/{staff.id}"
    ).status_code == 204
    assert client.delete(
        f"/programs/{program['id']}/roles/{creator.id}"
    ).status_code == 409


def test_submitter_role_conflicts_with_staff(db, client, user_factory):
    programmer = user_factory(username="submitter-programmer")
    submitter = user_factory(username="recorded-submitter")
    staff = user_factory(username="staff-cannot-submit")
    program = _create_program(client, programmer)

    assert client.post(
        f"/programs/{program['id']}/roles",
        json={"userId": staff.id, "roleType": "STAFF"},
    ).status_code == 200

    assert _login(client, submitter).status_code == 200
    assert client.post(
        f"/programs/{program['id']}/screenings",
        json={"filmTitle": "Owned Film"},
    ).status_code == 201

    role = ProgramRole.query.filter_by(
        program_id=program["id"], user_id=submitter.id
    ).first()
    assert role is None

    assert _login(client, programmer).status_code == 200
    assert client.post(
        f"/programs/{program['id']}/roles",
        json={"userId": submitter.id, "roleType": "STAFF"},
    ).status_code == 409

    assert _login(client, staff).status_code == 200
    assert client.post(
        f"/programs/{program['id']}/screenings",
        json={"filmTitle": "Conflict Film"},
    ).status_code == 403


def test_handler_requires_a_submitted_screening(db, client, user_factory):
    programmer = user_factory(username="handler-programmer")
    submitter = user_factory(username="handler-submitter")
    staff = user_factory(username="handler-staff")
    program = _create_program(client, programmer)

    assert client.post(
        f"/programs/{program['id']}/roles",
        json={"userId": staff.id, "roleType": "STAFF"},
    ).status_code == 200

    assert _login(client, submitter).status_code == 200
    draft = client.post(
        f"/programs/{program['id']}/screenings",
        json={"filmTitle": "Draft Film"},
    ).get_json()

    assert _login(client, programmer).status_code == 200
    for state in ("SUBMISSION", "ASSIGNMENT"):
        assert client.post(
            f"/programs/{program['id']}/transitions",
            json={"targetState": state},
        ).status_code == 200

    response = client.post(
        f"/programs/{program['id']}/screenings/{draft['id']}/handler",
        json={"userId": staff.id},
    )
    assert response.status_code == 409


def test_identical_screening_creation_is_not_executed_twice(
    db, client, user_factory
):
    programmer = user_factory(username="duplicate-programmer")
    submitter = user_factory(username="duplicate-submitter")
    program = _create_program(client, programmer)
    assert _login(client, submitter).status_code == 200
    payload = {
        "filmTitle": "One Request",
        "filmDurationMinutes": 90,
        "auditoriumName": "Hall A",
        "startTime": "2026-10-10T18:00:00",
    }

    first = client.post(f"/programs/{program['id']}/screenings", json=payload)
    second = client.post(f"/programs/{program['id']}/screenings", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert Screening.query.filter_by(program_id=program["id"]).count() == 1


def test_public_screening_does_not_expose_cast(db, client, user_factory):
    programmer = user_factory(username="public-programmer")
    submitter = user_factory(username="public-submitter")
    program = _create_program(client, programmer)

    screening = Screening(
        program_id=program["id"],
        submitter_id=submitter.id,
        film_title="Public Film",
        film_cast="Private Cast Details",
        film_genres="Drama",
        auditorium_name="Hall A",
        state=ScreeningState.SCHEDULED,
    )
    sqlalchemy_db.session.add(screening)
    stored = sqlalchemy_db.session.get(Program, program["id"])
    stored.state = ProgramState.ANNOUNCED
    sqlalchemy_db.session.commit()

    client.post("/auth/logout")
    response = client.get(f"/programs/{program['id']}/screenings/{screening.id}")
    assert response.status_code == 200
    assert "filmCast" not in response.get_json()


def test_program_search_rate_limit_returns_json(db, client):
    responses = [client.get("/programs") for _ in range(31)]
    assert all(response.status_code == 200 for response in responses[:30])
    assert responses[30].status_code == 429
    assert responses[30].is_json
    assert "error" in responses[30].get_json()
