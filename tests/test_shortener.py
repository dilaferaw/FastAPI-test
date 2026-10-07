# test_shortener.py


def test_shorten_basic(client):
    r = client.post("/shorten", json={"url": "https://example.com"})
    assert r.status_code == 201
    assert r.json()["created"] == True
    assert len(r.json()["code"]) == 6
    assert r.json()["short_url"].endswith(r.json()["code"])


def test_shorten_idempotent(client):
    r = client.post("/shorten", json={"url": "https://example.com"})
    r2 = client.post("/shorten", json={"url": "https://example.com"})

    assert r.json()["code"] == r2.json()["code"]
    assert r2.json()["created"] == False


def test_shorten_custom_code(client):
    custom_code = "dilla"
    r = client.post(
        "/shorten", json={"url": "https://example.com", "custom_code": custom_code}
    )
    assert r.json()["code"] == custom_code


def test_shorten_custom_code_collision(client):
    custom_code = "dilla"
    r = client.post(
        "/shorten", json={"url": "https://example.com", "custom_code": custom_code}
    )
    custom_code_2 = "dilla"
    r2 = client.post(
        "/shorten",
        json={"url": "https://anotherexample.com", "custom_code": custom_code_2},
    )

    assert r.status_code == 201
    assert r2.status_code == 409


def test_shorten_reserved_code(client):
    reserved_code = "docs"
    r = client.post(
        "/shorten", json={"url": "https://example.com", "custom_code": reserved_code}
    )

    assert r.status_code == 409


def test_shorten_bad_scheme(client):
    r = client.post("/shorten", json={"url": "javascript:alert(1)"})

    assert r.status_code == 422


def test_shorten_missing_url(client):
    r = client.post("/shorten", json={})
    assert r.status_code == 422


def test_shorten_invalid_custom_code(client):
    r = client.post(
        "/shorten", json={"url": "https://example.com", "custom_code": "DILA"}
    )

    r2 = client.post(
        "/shorten", json={"url": "https://example.com", "custom_code": "ab"}
    )
    assert r.status_code == 422
    assert r2.status_code == 422


def test_redirect_success(client):
    r = client.post("/shorten", json={"url": "https://example.com"})
    code = r.json()["code"]
    original = r.json()["original_url"]

    r2 = client.get(f"/{code}", follow_redirects=False)
    assert r2.status_code == 302
    assert r2.headers["location"] == original


def test_redirect_missing(client):
    r = client.get("/nonexsistent")
    assert r.status_code == 404


# There is slim but certain probability that the random code generator
# will create duplicate codes for different url but this is resolved by
# the if statments which filter these kind of cases in the "/shorten"
# endpoint. unless the generator exhausts all the possible combinations of codes, which is very unlikely to happen.
def test_random_code_is_random(client):
    r = client.post("/shorten", json={"url": "https://example.com"})
    r2 = client.post("/shorten", json={"url": "https://example2.com"})
    assert r.json()["code"] != r2.json()["code"]
