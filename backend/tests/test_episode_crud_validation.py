from tests.conftest import EDITOR_HEADERS


def _make_show(client, slug="show-a", section="series"):
    r = client.post("/admin/shows", headers=EDITOR_HEADERS, json={
        "slug": slug, "title": "Show A", "section": section, "synopsis": "", "categories": [],
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_cannot_publish_without_duration(client):
    show_id = _make_show(client)
    r = client.post("/admin/episodes", headers=EDITOR_HEADERS, json={
        "episode_id": "ep_a", "show_id": show_id, "season_number": 1, "episode_number": 1,
        "episode_title": "Ep A", "duration_seconds": None, "language": "en",
        "content_group": "cg-a", "status": "published",
    })
    assert r.status_code == 409
    assert any("duration" in m for m in r.json()["detail"])


def test_cannot_publish_without_artwork(client):
    show_id = _make_show(client)
    r = client.post("/admin/episodes", headers=EDITOR_HEADERS, json={
        "episode_id": "ep_b", "show_id": show_id, "season_number": 1, "episode_number": 1,
        "episode_title": "Ep B", "duration_seconds": 100, "language": "en",
        "content_group": "cg-b", "status": "published",
    })
    assert r.status_code == 409
    assert any("artwork" in m for m in r.json()["detail"])


def test_cannot_publish_show_without_section(client):
    show_id = _make_show(client, slug="show-nosection", section=None)
    r = client.post("/admin/episodes", headers=EDITOR_HEADERS, json={
        "episode_id": "ep_c", "show_id": show_id, "season_number": 1, "episode_number": 1,
        "episode_title": "Ep C", "duration_seconds": 100, "language": "en",
        "content_group": "cg-c", "status": "published",
    })
    assert r.status_code == 409
    assert any("section" in m for m in r.json()["detail"])


def _upload_all_artwork(client, episode_pk):
    from pathlib import Path
    assets = Path(__file__).resolve().parent.parent.parent / "assets_seed"
    files = {"poster": "poster_good.jpg", "banner": "banner_good.jpg", "thumbnail": "thumb_good.jpg"}
    for kind, fname in files.items():
        with open(assets / fname, "rb") as f:
            r = client.post(
                f"/admin/episodes/{episode_pk}/artwork", headers=EDITOR_HEADERS,
                data={"kind": kind}, files={"file": (fname, f, "image/jpeg")},
            )
            assert r.status_code == 201, r.text


def test_publish_succeeds_with_all_preconditions_met(client):
    show_id = _make_show(client, slug="show-d")
    r = client.post("/admin/episodes", headers=EDITOR_HEADERS, json={
        "episode_id": "ep_d", "show_id": show_id, "season_number": 1, "episode_number": 1,
        "episode_title": "Ep D", "duration_seconds": 100, "language": "en",
        "content_group": "cg-d", "status": "draft",
    })
    assert r.status_code == 201
    ep_pk = r.json()["id"]
    _upload_all_artwork(client, ep_pk)

    r2 = client.patch(f"/admin/episodes/{ep_pk}", headers=EDITOR_HEADERS, json={"status": "published"})
    assert r2.status_code == 200, r2.text


def test_duplicate_content_group_language_rejected_on_create(client):
    show_id = _make_show(client, slug="show-e")
    r = client.post("/admin/episodes", headers=EDITOR_HEADERS, json={
        "episode_id": "ep_e1", "show_id": show_id, "season_number": 1, "episode_number": 1,
        "episode_title": "Ep E1", "duration_seconds": 100, "language": "en",
        "content_group": "cg-e", "status": "draft",
    })
    ep_pk = r.json()["id"]
    _upload_all_artwork(client, ep_pk)
    r2 = client.patch(f"/admin/episodes/{ep_pk}", headers=EDITOR_HEADERS, json={"status": "published"})
    assert r2.status_code == 200

    r3 = client.post("/admin/episodes", headers=EDITOR_HEADERS, json={
        "episode_id": "ep_e2", "show_id": show_id, "season_number": 1, "episode_number": 2,
        "episode_title": "Ep E2", "duration_seconds": 100, "language": "en",
        "content_group": "cg-e", "status": "draft",
    })
    ep2_pk = r3.json()["id"]
    _upload_all_artwork(client, ep2_pk)
    r4 = client.patch(f"/admin/episodes/{ep2_pk}", headers=EDITOR_HEADERS, json={"status": "published"})
    assert r4.status_code == 409
    assert any("content_group" in m for m in r4.json()["detail"])


def test_invalid_section_rejected_with_readable_error(client):
    r = client.post("/admin/shows", headers=EDITOR_HEADERS, json={
        "slug": "bad-section-show", "title": "Bad", "section": "not-real", "synopsis": "", "categories": [],
    })
    assert r.status_code == 422
    assert "not-real" in r.json()["detail"][0]


def test_invalid_language_rejected(client):
    show_id = _make_show(client, slug="show-f")
    r = client.post("/admin/episodes", headers=EDITOR_HEADERS, json={
        "episode_id": "ep_f", "show_id": show_id, "season_number": 1, "episode_number": 1,
        "episode_title": "Ep F", "duration_seconds": 100, "language": "fr",
        "content_group": "cg-f", "status": "draft",
    })
    assert r.status_code == 422