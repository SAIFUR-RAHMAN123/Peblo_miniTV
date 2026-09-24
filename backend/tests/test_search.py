from tests.conftest import ADMIN_HEADERS, EDITOR_HEADERS
from tests.test_episode_crud_validation import _make_show, _upload_all_artwork


def _seed_two_searchable_episodes(client):
    show1 = _make_show(client, slug="moti-show", section="series")
    r = client.post("/admin/shows", headers=EDITOR_HEADERS, json={
        "slug": "song-show", "title": "Song Time", "section": "songs", "synopsis": "", "categories": ["music"],
    })
    show2 = r.json()["id"]
    client.patch(f"/admin/shows/{show1}", headers=EDITOR_HEADERS, json={"categories": ["adventure"]})

    for ep_id, show_id, lang, title, cg in [
        ("ep_s1", show1, "en", "Moti Goes Home", "cg-s1"),
        ("ep_s2", show2, "hi", "Gaana Time", "cg-s2"),
    ]:
        r = client.post("/admin/episodes", headers=EDITOR_HEADERS, json={
            "episode_id": ep_id, "show_id": show_id, "season_number": 1, "episode_number": 1,
            "episode_title": title, "duration_seconds": 100, "language": lang,
            "content_group": cg, "status": "draft",
        })
        ep_pk = r.json()["id"]
        _upload_all_artwork(client, ep_pk)
        client.patch(f"/admin/episodes/{ep_pk}", headers=EDITOR_HEADERS, json={"status": "published"})

    client.post("/admin/catalog/publish", headers=ADMIN_HEADERS)


def test_search_by_show_title(client):
    _seed_two_searchable_episodes(client)
    r = client.get("/catalog/search", params={"q": "moti"})
    assert r.json()["count"] == 1
    assert r.json()["results"][0]["show_slug"] == "moti-show"


def test_search_by_episode_title(client):
    _seed_two_searchable_episodes(client)
    r = client.get("/catalog/search", params={"q": "gaana"})
    assert r.json()["count"] == 1


def test_search_by_category(client):
    _seed_two_searchable_episodes(client)
    r = client.get("/catalog/search", params={"q": "music"})
    assert r.json()["count"] == 1
    assert r.json()["results"][0]["show_slug"] == "song-show"


def test_filters_compose_with_and(client):
    _seed_two_searchable_episodes(client)
    r = client.get("/catalog/search", params={"section": "songs", "language": "hi"})
    assert r.json()["count"] == 1
    r2 = client.get("/catalog/search", params={"section": "songs", "language": "en"})
    assert r2.json()["count"] == 0


def test_empty_search_returns_all(client):
    _seed_two_searchable_episodes(client)
    r = client.get("/catalog/search")
    assert r.json()["count"] == 2