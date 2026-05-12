import pytest

from meters.models import Meter


@pytest.mark.django_db
def test_list_meters_owner_scoped(authed_client, meter, other_meter):
    resp = authed_client.get("/api/meters/")
    assert resp.status_code == 200
    body = resp.json()
    numbers = [m["meter_number"] for m in body]
    assert meter.meter_number in numbers
    assert other_meter.meter_number not in numbers


@pytest.mark.django_db
def test_create_meter(authed_client, user):
    resp = authed_client.post(
        "/api/meters/",
        {"meter_number": "0900000001", "label": "Shop"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["meter_number"] == "0900000001"
    assert Meter.objects.filter(meter_number="0900000001", owner=user).exists()


@pytest.mark.django_db
def test_create_meter_rejects_non_digit(authed_client):
    resp = authed_client.post(
        "/api/meters/",
        {"meter_number": "ABC1234567"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_retrieve_other_users_meter_404s(authed_client, other_meter):
    resp = authed_client.get(f"/api/meters/{other_meter.id}/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_delete_meter(authed_client, meter):
    resp = authed_client.delete(f"/api/meters/{meter.id}/")
    assert resp.status_code == 204
    assert not Meter.objects.filter(id=meter.id).exists()


@pytest.mark.django_db
def test_unauthed_list_rejected(api_client):
    resp = api_client.get("/api/meters/")
    assert resp.status_code == 401
