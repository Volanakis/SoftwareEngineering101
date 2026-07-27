def _log_in(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id


def _valid_payload(**overrides):
    payload = {
        "name": "Spring Season",
        "description": "A season of films",
        "startDate": "2026-01-01",
        "endDate": "2026-06-30",
    }
    payload.update(overrides)
    return payload


def test_create_program_requires_authentication(db, client):
    response = client.post("/programs", json=_valid_payload())

    assert response.status_code == 401


def test_create_program_success(db, user_factory, client):
    creator = user_factory(username="creator")
    _log_in(client, creator)

    response = client.post("/programs", json=_valid_payload())

    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "Spring Season"
    assert body["state"] == "CREATED"
    assert [p["username"] for p in body["programmers"]] == ["creator"]


def test_create_program_missing_field_returns_400(db, user_factory, client):
    creator = user_factory(username="creator")
    _log_in(client, creator)

    response = client.post("/programs", json=_valid_payload(name=""))

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_program_duplicate_name_returns_409(db, user_factory, client):
    creator = user_factory(username="creator")
    _log_in(client, creator)
    client.post("/programs", json=_valid_payload())

    response = client.post("/programs", json=_valid_payload())

    assert response.status_code == 409


def test_get_program_redacted_for_visitor(db, user_factory, client):
    creator = user_factory(username="creator")
    _log_in(client, creator)
    created = client.post("/programs", json=_valid_payload()).get_json()

    with client.session_transaction() as sess:
        sess.clear()

    response = client.get(f"/programs/{created['id']}")

    assert response.status_code == 200
    body = response.get_json()
    assert "programmers" not in body


def test_get_program_not_found_returns_404(db, client):
    response = client.get("/programs/does-not-exist")

    assert response.status_code == 404


def test_search_programs_returns_results_list(db, user_factory, client):
    creator = user_factory(username="creator")
    _log_in(client, creator)
    client.post("/programs", json=_valid_payload())

    response = client.get("/programs")

    assert response.status_code == 200
    assert len(response.get_json()["results"]) == 1


def test_search_programs_filters_by_name(db, user_factory, client):
    creator = user_factory(username="creator")
    _log_in(client, creator)
    client.post("/programs", json=_valid_payload(name="Spring"))
    client.post("/programs", json=_valid_payload(name="Autumn"))

    response = client.get("/programs", query_string={"name": "Autumn"})

    results = response.get_json()["results"]
    assert [p["name"] for p in results] == ["Autumn"]


def test_update_program_success(db, user_factory, client):
    creator = user_factory(username="creator")
    _log_in(client, creator)
    created = client.post("/programs", json=_valid_payload()).get_json()

    response = client.put(
        f"/programs/{created['id']}", json={"description": "Updated"}
    )

    assert response.status_code == 200
    assert response.get_json()["description"] == "Updated"


def test_update_program_forbidden_for_non_programmer(db, user_factory, client):
    creator = user_factory(username="creator")
    outsider = user_factory(username="outsider")
    _log_in(client, creator)
    created = client.post("/programs", json=_valid_payload()).get_json()

    _log_in(client, outsider)
    response = client.put(f"/programs/{created['id']}", json={"description": "Nope"})

    assert response.status_code == 403


def test_delete_program_success(db, user_factory, client):
    creator = user_factory(username="creator")
    _log_in(client, creator)
    created = client.post("/programs", json=_valid_payload()).get_json()

    response = client.delete(f"/programs/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/programs/{created['id']}").status_code == 404


def test_delete_program_forbidden_for_non_programmer(db, user_factory, client):
    creator = user_factory(username="creator")
    outsider = user_factory(username="outsider")
    _log_in(client, creator)
    created = client.post("/programs", json=_valid_payload()).get_json()

    _log_in(client, outsider)
    response = client.delete(f"/programs/{created['id']}")

    assert response.status_code == 403


def test_add_role_programmer(db, user_factory, client):
    creator = user_factory(username="creator")
    new_programmer = user_factory(username="new-programmer")
    _log_in(client, creator)
    created = client.post("/programs", json=_valid_payload()).get_json()

    response = client.post(
        f"/programs/{created['id']}/roles",
        json={"userId": new_programmer.id, "roleType": "PROGRAMMER"},
    )

    assert response.status_code == 200
    usernames = {p["username"] for p in response.get_json()["programmers"]}
    assert usernames == {"creator", "new-programmer"}


def test_add_role_staff(db, user_factory, client):
    creator = user_factory(username="creator")
    staff_member = user_factory(username="staffer")
    _log_in(client, creator)
    created = client.post("/programs", json=_valid_payload()).get_json()

    response = client.post(
        f"/programs/{created['id']}/roles",
        json={"userId": staff_member.id, "roleType": "STAFF"},
    )

    assert response.status_code == 200
    assert [s["username"] for s in response.get_json()["staff"]] == ["staffer"]


def test_add_role_invalid_role_type_returns_400(db, user_factory, client):
    creator = user_factory(username="creator")
    target = user_factory(username="target")
    _log_in(client, creator)
    created = client.post("/programs", json=_valid_payload()).get_json()

    response = client.post(
        f"/programs/{created['id']}/roles",
        json={"userId": target.id, "roleType": "OWNER"},
    )

    assert response.status_code == 400


def test_add_role_duplicate_returns_409(db, user_factory, client):
    creator = user_factory(username="creator")
    _log_in(client, creator)
    created = client.post("/programs", json=_valid_payload()).get_json()

    response = client.post(
        f"/programs/{created['id']}/roles",
        json={"userId": creator.id, "roleType": "PROGRAMMER"},
    )

    assert response.status_code == 409


def test_transition_program_success(db, user_factory, client):
    creator = user_factory(username="creator")
    _log_in(client, creator)
    created = client.post("/programs", json=_valid_payload()).get_json()

    response = client.post(
        f"/programs/{created['id']}/transitions", json={"targetState": "SUBMISSION"}
    )

    assert response.status_code == 200
    assert response.get_json()["state"] == "SUBMISSION"


def test_transition_program_rejects_skip(db, user_factory, client):
    creator = user_factory(username="creator")
    _log_in(client, creator)
    created = client.post("/programs", json=_valid_payload()).get_json()

    response = client.post(
        f"/programs/{created['id']}/transitions", json={"targetState": "ASSIGNMENT"}
    )

    assert response.status_code == 409


def test_transition_program_missing_target_state_returns_400(db, user_factory, client):
    creator = user_factory(username="creator")
    _log_in(client, creator)
    created = client.post("/programs", json=_valid_payload()).get_json()

    response = client.post(f"/programs/{created['id']}/transitions", json={})

    assert response.status_code == 400
