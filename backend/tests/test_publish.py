from tests.conftest import ADMIN_HEADERS, EDITOR_HEADERS
from tests.test_episode_crud_validation import _make_show, _upload_all_artwork


def _publish_ready_episode(client, slug, ep_id, cg, section="series"):
    show_id = _make_show(client, slug=slug, section=section)
    r = client.post("/admin/episodes", headers=EDITOR_HEADERS, json={
        "episode_id": ep_id, "show_id": show_id, "season_number": 1, "episode_number": 1,
        "episode_title": "Title", "duration_seconds": 100, "language": "en",
        "content_group": cg, "status": "draft",
    })
    ep_pk = r.json()["id"]
    _upload_all_artwork(client, ep_pk)
    r2 = client.patch(f"/admin/episodes/{ep_pk}", headers=EDITOR_HEADERS, json={"status": "published"})
    assert r2.status_code == 200, r2.text
    return show_id, ep_pk


def test_publish_blocked_when_validation_report_has_issues(client, db):
    from app.models import Episode
    _publish_ready_episode(client, "show-p1", "ep_p1", "cg-p1")
    ep = db.query(Episode).filter(Episode.episode_id == "ep_p1").first()
    dupe = Episode(
        episode_id="ep_p1_dupe", show_id=ep.show_id, season_number=1, episode_number=2,
        episode_title="Dupe", duration_seconds=100, language="en",
        content_group="cg-p1", status="published",
    )
    db.add(dupe)
    db.commit()

    r = client.post("/admin/catalog/publish", headers=ADMIN_HEADERS)
    assert r.status_code == 201
    body = r.json()
    assert body["outcome"] == "failed"
    assert body["reason"] == "blocked_by_validation"
    assert len(body["issues"]) >= 1


def test_publish_succeeds_and_catalog_reflects_it(client):
    _publish_ready_episode(client, "show-p2", "ep_p2", "cg-p2", section="songs")
    r = client.post("/admin/catalog/publish", headers=ADMIN_HEADERS)
    assert r.status_code == 201
    body = r.json()
    assert body["outcome"] == "success"
    assert body["episodes_count"] == 1

    cat = client.get("/catalog").json()
    assert len(cat["entries"]) == 1
    assert cat["entries"][0]["show_slug"] == "show-p2"
    assert cat["sections"][0]["section"] == "songs"


def test_blocked_publish_does_not_overwrite_existing_good_catalog(client, db):
    from app.models import Episode
    _publish_ready_episode(client, "show-p3", "ep_p3", "cg-p3")
    r1 = client.post("/admin/catalog/publish", headers=ADMIN_HEADERS)
    assert r1.json()["outcome"] == "success"
    first_catalog = client.get("/catalog").json()
    assert len(first_catalog["entries"]) == 1

    ep = db.query(Episode).filter(Episode.episode_id == "ep_p3").first()
    dupe = Episode(
        episode_id="ep_p3_dupe", show_id=ep.show_id, season_number=1, episode_number=2,
        episode_title="Dupe", duration_seconds=100, language="en",
        content_group="cg-p3", status="published",
    )
    db.add(dupe)
    db.commit()

    r2 = client.post("/admin/catalog/publish", headers=ADMIN_HEADERS)
    assert r2.json()["outcome"] == "failed"

    second_catalog = client.get("/catalog").json()
    assert second_catalog == first_catalog


def test_language_variants_collapse_into_one_entry(client):
    show_id = _make_show(client, slug="show-p4")
    for lang, ep_id in [("en", "ep_p4_en"), ("hi", "ep_p4_hi")]:
        r = client.post("/admin/episodes", headers=EDITOR_HEADERS, json={
            "episode_id": ep_id, "show_id": show_id, "season_number": 1, "episode_number": 1,
            "episode_title": "Same Episode", "duration_seconds": 100, "language": lang,
            "content_group": "cg-p4-shared", "status": "draft",
        })
        ep_pk = r.json()["id"]
        _upload_all_artwork(client, ep_pk)
        client.patch(f"/admin/episodes/{ep_pk}", headers=EDITOR_HEADERS, json={"status": "published"})

    r = client.post("/admin/catalog/publish", headers=ADMIN_HEADERS)
    assert r.json()["outcome"] == "success"
    assert r.json()["episodes_count"] == 1

    cat = client.get("/catalog").json()
    assert len(cat["entries"]) == 1
    langs = {l["language"] for l in cat["entries"][0]["languages"]}
    assert langs == {"en", "hi"}


def test_season_zero_goes_to_trailers_not_seasons(client):
    show_id = _make_show(client, slug="show-p5")
    r = client.post("/admin/episodes", headers=EDITOR_HEADERS, json={
        "episode_id": "ep_p5_trailer", "show_id": show_id, "season_number": 0, "episode_number": 1,
        "episode_title": "Trailer", "duration_seconds": 30, "language": "en",
        "content_group": "cg-p5-trailer", "status": "draft",
    })
    ep_pk = r.json()["id"]
    _upload_all_artwork(client, ep_pk)
    client.patch(f"/admin/episodes/{ep_pk}", headers=EDITOR_HEADERS, json={"status": "published"})

    r2 = client.post("/admin/catalog/publish", headers=ADMIN_HEADERS)
    assert r2.json()["outcome"] == "success"

    cat = client.get("/catalog").json()
    show_entry = cat["sections"][0]["shows"][0]
    assert show_entry["seasons"] == []
    assert len(show_entry["trailers"]) == 1