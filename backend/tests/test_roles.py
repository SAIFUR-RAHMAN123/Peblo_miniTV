def test_no_auth_rejected(client):
    r = client.get("/admin/shows")
    assert r.status_code == 401


def test_bad_key_rejected(client):
    r = client.get("/admin/shows", headers={"Authorization": "Bearer wrong-key"})
    assert r.status_code == 401


def test_editor_can_crud(client):
    from tests.conftest import EDITOR_HEADERS
    r = client.get("/admin/shows", headers=EDITOR_HEADERS)
    assert r.status_code == 200


def test_editor_cannot_publish(client):
    from tests.conftest import EDITOR_HEADERS
    r = client.post("/admin/catalog/publish", headers=EDITOR_HEADERS)
    assert r.status_code == 403


def test_admin_can_publish_endpoint(client):
    from tests.conftest import ADMIN_HEADERS
    r = client.post("/admin/catalog/publish", headers=ADMIN_HEADERS)
    assert r.status_code == 201  # succeeds trivially with zero published episodes


def test_admin_can_also_do_editor_actions(client):
    from tests.conftest import ADMIN_HEADERS
    r = client.get("/admin/shows", headers=ADMIN_HEADERS)
    assert r.status_code == 200


def test_catalog_is_public_no_auth(client):
    r = client.get("/catalog")
    assert r.status_code == 200