import pytest

# Part 4 Happy Path Tests


def test_list_artworks_empty(client):
    response = client.get("/artworks/")

    assert response.status_code == 200
    assert response.json() == []

def test_get_seeded_artwork(client, seeded_db):
    # Arrange: seeded_db has already loaded the 11 artworks (the Mona Lisa is first)
    expected = {"id": 1, **seeded_db[0]}

    # Act
    response = client.get("/artworks/1")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected

def test_create_artwork(client, sample_artwork):
    #Act
    response = client.post("/artworks/", json=sample_artwork)

    # Assert
    assert response.status_code == 201

    data = response.json()

    assert isinstance(data["id"], int)

    for field, value in sample_artwork.items():
        assert data[field] == value

def test_create_artwork_is_saved(client, created_artwork):
    #Act
    artwork_id = created_artwork["id"]
    response = client.get(f"/artworks/{artwork_id}")

    # Assert
    assert response.status_code == 200
    assert response.json() == created_artwork

def test_update_artwork(client, created_artwork, updated_artwork):
    #Arrange
    artwork_id = created_artwork["id"]

    #Act
    response = client.put(
        f"/artworks/{artwork_id}",
        json=updated_artwork
    )

    # Assert
    expected = {"id": artwork_id, **updated_artwork}

    assert response.status_code == 200
    assert response.json() == expected

    #Verify that the changes were actually saved
    get_response = client.get(f"/artworks/{artwork_id}")

    assert get_response.status_code == 200
    assert get_response.json() == expected

def test_delete_artwork(client, created_artwork):
    #Arrange
    artwork_id = created_artwork["id"]

    #Act
    response = client.delete(f"/artworks/{artwork_id}")

    #Assert
    assert response.status_code == 204
    assert response.content == b""

    #Verify that the artwork was actually deleted
    get_response = client.get(f"/artworks/{artwork_id}")

    assert get_response.status_code == 404

# Part 5 Unhappy Path Tests

@pytest.mark.parametrize(
    "method, use_body",
    [
        ("get", False),
        ("put", True),
        ("delete", False)
    ],
    ids=["get", "put", "delete"], 
)
def test_artwork_not_found(client, sample_artwork, method, use_body):
    #Arrange
    kwargs = {"json": sample_artwork} if use_body else {}

    #Act
    response = client.request(method, "/artworks/9999", **kwargs)

    #Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Artwork not found"}

def test_non_integer_id(client):
    # Act
    response = client.get("/artworks/mona-lisa")

    # Assert
    assert response.status_code == 422

def test_create_duplicate(client, created_artwork, sample_artwork):
    # Act
    response = client.post("/artworks/", json=sample_artwork)

    # Assert
    assert response.status_code == 409
    assert response.json() == {
        "detail": "An artwork with that title and artist already exists"
    }

def test_create_duplicate_ignores_case(client, created_artwork, sample_artwork):
    # Arrange
    duplicate_artwork = sample_artwork.copy()
    duplicate_artwork["title"] = duplicate_artwork["title"].upper()
    duplicate_artwork["artist"] = duplicate_artwork["artist"].lower()

    # Act
    response = client.post("/artworks/", json=duplicate_artwork)

    # Assert
    assert response.status_code == 409
    assert response.json() == {
        "detail": "An artwork with that title and artist already exists"
    }

def test_update_into_duplicate(client, seeded_db):
    #Arrange:
    mono_lisa = client.get("/artworks/1").json()

    duplicate_artwork = {
        key: value
        for key, value in mono_lisa.items()
        if key != "id"
    }

    #Act
    response = client.put("/artworks/2", json=duplicate_artwork)

    #Assert
    assert response.status_code == 409

    #Verify that the artwork dos wasn't changed
    get_response = client.get("/artworks/2")

    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Lady with an Ermine"
    assert get_response.json()["artist"] == "Leonardo da Vinci"

def test_update_same_title_and_artist_is_allowed(client, created_artwork):
    #Arrange
    artwork_id = created_artwork["id"]

    same_artwork = {
        key: value
        for key, value in created_artwork.items()
        if key != "id"
    }

    same_artwork["museum"] = "Different Museum"

    #Act
    response = client.put(
        f"/artworks/{artwork_id}",
        json=same_artwork
    )

    #Assert
    expected = {"id": artwork_id, **same_artwork}

    assert response.status_code == 200
    assert response.json() == expected

    # Part 6 Parameterized Tests

@pytest.mark.parametrize(
    "missing_field",
    [
        "title",
        "artist",
        "year",
        "medium",
        "museum",
        "image_url",
    ],
    ids=[
        "missing-title",
        "missing-artist",
        "missing-year",
        "missing-medium",
        "missing-museum",
        "missing-image-url",
    ],
)

def test_create_missing_field(client, sample_artwork, missing_field):
    #Arrange
    invalid_artwork = sample_artwork.copy()
    invalid_artwork.pop(missing_field)

    #Act
    response = client.post("/artworks/", json=invalid_artwork)

    #Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", missing_field]

@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("year", 3000),
        ("year", "nineteen-oh-seven"),
        ("title", ""),
    ],
    ids=["future-year", "year-not-number", "empty-title"],
)
def test_create_invalid_value(client, sample_artwork, field, bad_value):
    # Arrange
    invalid_artwork = sample_artwork.copy()
    invalid_artwork[field] = bad_value

    # Act
    response = client.post("/artworks/", json=invalid_artwork)

    # Assert
    assert response.status_code == 422

@pytest.mark.parametrize(
    "skip, limit, expected_count",
    [
        (0, 3, 3),
        (3, 4, 4),
        (0, 0, 0),
        (11, 3, 0),
    ],
    ids=["first-three", "skip-three-get-four", "zero-limit", "past-end"],
)

def test_pagination_counts(client, seeded_db, skip, limit, expected_count):
    # Arrange
    params = {"skip": skip, "limit": limit}

    # Act
    response = client.get("/artworks/", params=params)

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == expected_count

@pytest.mark.parametrize(
    "params",
    [
        {"skip": -1},
        {"limit": 500},
    ],
    ids=["negative-skip", "limit-too-high"],
)

def test_pagination_invalid(client, params):
    # Act
    response = client.get("/artworks/", params=params)

    # Assert
    assert response.status_code == 422

@pytest.mark.parametrize(
    "artist, expected_titles",
    [
        (
            "Claude Monet",
            [
                "Impression, Sunrise",
                "Woman with a Parasol – Madame Monet and Her Son",
            ],
        ),
        (
            "da vinci",
            [
                "Mona Lisa",
                "Lady with an Ermine",
            ],
        ),
        (
            "Unknown Artist",
            [],
        ),
    ],
    ids=["exact-name", "lowercase-partial", "no-match"],
)
def test_filter_by_artist(client, seeded_db, artist, expected_titles):
    # Arrange
    params = {"artist": artist}

    # Act
    response = client.get("/artworks/", params=params)

    # Assert
    assert response.status_code == 200

    actual_titles = [artwork["title"] for artwork in response.json()]

    assert actual_titles == expected_titles