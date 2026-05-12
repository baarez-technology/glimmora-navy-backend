def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["version"] == "1.0.0"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "aegis-api"}


def test_docs_available(client):
    assert client.get("/docs").status_code == 200


def test_openapi_schema(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert r.json()["info"]["title"] == "GLIMMORA AEGIS — Navy Training Platform API"
