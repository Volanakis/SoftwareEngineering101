from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.program import Program, ProgramRole, ProgramState, RoleType


def _make_program(name="Spring Season", **overrides):
    defaults = dict(
        name=name,
        description="A season of films",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 30),
    )
    defaults.update(overrides)
    return Program(**defaults)


def test_program_defaults(db):
    program = _make_program()
    db.session.add(program)
    db.session.commit()

    assert program.id is not None
    assert program.creation_date is not None
    assert program.state == ProgramState.CREATED


def test_program_name_must_be_unique(db):
    db.session.add(_make_program(name="Spring"))
    db.session.commit()

    db.session.add(_make_program(name="Spring"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_program_role_assigns_programmer(db, user_factory):
    program = _make_program()
    db.session.add(program)
    creator = user_factory(username="creator")
    db.session.add(ProgramRole(program=program, user=creator, role_type=RoleType.PROGRAMMER))
    db.session.commit()

    assert program.programmers == [creator]
    assert program.staff == []


def test_program_role_assigns_staff(db, user_factory):
    program = _make_program()
    db.session.add(program)
    staff_member = user_factory(username="staffer")
    db.session.add(ProgramRole(program=program, user=staff_member, role_type=RoleType.STAFF))
    db.session.commit()

    assert program.staff == [staff_member]
    assert program.programmers == []


def test_user_can_have_at_most_one_role_per_program(db, user_factory):
    program = _make_program()
    db.session.add(program)
    user = user_factory(username="dual")
    db.session.add(ProgramRole(program=program, user=user, role_type=RoleType.PROGRAMMER))
    db.session.commit()

    db.session.add(ProgramRole(program=program, user=user, role_type=RoleType.STAFF))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_user_can_have_different_roles_in_different_programs(db, user_factory):
    program_one = _make_program(name="Spring")
    program_two = _make_program(name="Autumn")
    db.session.add_all([program_one, program_two])
    user = user_factory(username="multi")
    db.session.add(ProgramRole(program=program_one, user=user, role_type=RoleType.PROGRAMMER))
    db.session.add(ProgramRole(program=program_two, user=user, role_type=RoleType.STAFF))
    db.session.commit()

    assert program_one.programmers == [user]
    assert program_two.staff == [user]
