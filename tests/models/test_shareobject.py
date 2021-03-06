import pytest
from datetime import datetime

from share.models import Person
from share.models.base import ShareObject
from share.management.commands.maketriggermigrations import Command


@pytest.mark.django_db
def test_build_trigger():
    assert issubclass(Person, ShareObject)

    trigger_build = Command()
    procedure, trigger = trigger_build.build_operations(Person)

    assert trigger.reversible is True
    assert 'DROP TRIGGER share_person_change' in trigger.reverse_sql
    assert 'DROP TRIGGER IF EXISTS share_person_change' in trigger.sql

    assert procedure.reversible is True
    assert 'DROP FUNCTION before_share_person_change' in procedure.reverse_sql
    assert 'CREATE OR REPLACE FUNCTION before_share_person_change' in procedure.sql


@pytest.mark.django_db
def test_timestamping(share_source):
    p = Person(given_name='John', family_name='Doe', source=share_source)
    p.save()

    now = datetime.utcnow().replace(tzinfo=p.date_modified.tzinfo)
    created, modified = p.date_created, p.date_modified

    assert (p.date_created - p.date_modified).total_seconds() < 1

    p.given_name = 'Jane'
    p.save()

    assert modified < p.date_modified
    assert created == p.date_created


@pytest.mark.django_db
def test_create_version(share_source):
    p = Person(given_name='John', family_name='Doe', source=share_source)
    p.save()
    p.refresh_from_db()

    assert isinstance(p.version, Person.VersionModel)


@pytest.mark.django_db
def test_versioning(share_source):
    p = Person(given_name='John', family_name='Doe', source=share_source)
    p.save()

    p.given_name = 'Jane'
    p.save()

    assert p.versions.all()[0].given_name == 'Jane'
    assert p.versions.all()[1].given_name == 'John'
