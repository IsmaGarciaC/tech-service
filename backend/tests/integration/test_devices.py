from fastapi.testclient import TestClient

DEVICES = "/api/v1/devices"
MAX_ID = 2**63 - 1


def create_customer(client: TestClient) -> int:
    response = client.post("/api/v1/customers", json={"name": "Demo", "phone": "000"})
    assert response.status_code == 201
    return response.json()["id"]


def create_device(client: TestClient, customer_id: int, **fields: str) -> dict:
    payload = {"customer_id": customer_id, "device_type": "Laptop", **fields}
    response = client.post(DEVICES, json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_list_filter_and_paginate(client: TestClient) -> None:
    first, second = create_customer(client), create_customer(client)
    # Interleave owners so filtering after pagination would return the wrong page.
    owners = [first, second] * 11
    devices = [
        create_device(client, owner, serial_number="DEMO-01") for owner in owners
    ]
    ids = [device["id"] for device in devices]
    assert ids == sorted(set(ids))
    assert [device["customer_id"] for device in devices] == owners
    # Updating the first row changes its physical position in PostgreSQL.
    updated = client.patch(f"{DEVICES}/{ids[0]}", json={"brand": "Demo"})
    assert updated.status_code == 200
    devices[0] = updated.json()

    first_page = client.get(DEVICES)
    assert first_page.status_code == 200
    assert first_page.json() == devices[:20]
    page = client.get(DEVICES, params={"customer_id": first, "limit": 2, "offset": 1})
    assert page.status_code == 200
    assert page.json() == [devices[2], devices[4]]
    empty = client.get(DEVICES, params={"customer_id": MAX_ID})
    assert empty.status_code == 200
    assert empty.json() == []


def test_read_and_patch_descriptions_preserve_owner(client: TestClient) -> None:
    owner = create_customer(client)
    device = create_device(
        client, owner, device_type=" Laptop ", brand="  ", model=" Model A "
    )
    expected = {
        "id": device["id"],
        "customer_id": owner,
        "device_type": "Laptop",
        "brand": "",
        "model": "Model A",
        "serial_number": None,
    }
    assert device == expected
    path = f"{DEVICES}/{device['id']}"
    for changes in [
        {"device_type": "Notebook", "brand": "Demo", "serial_number": "001"},
        {"model": "Model B"},
        {"brand": None, "model": None, "serial_number": None},
        {},
    ]:
        expected.update(changes)
        patched = client.patch(path, json=changes)
        assert patched.status_code == 200
        assert patched.json() == expected
        fetched = client.get(path)
        assert fetched.status_code == 200
        assert fetched.json() == expected


def test_missing_owner_and_missing_device(client: TestClient) -> None:
    response = client.post(DEVICES, json={"customer_id": MAX_ID, "device_type": "PC"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}
    assert client.get(DEVICES).json() == []
    path = f"{DEVICES}/{MAX_ID}"
    assert client.get(path).status_code == 404
    assert client.patch(path, json={"brand": None}).status_code == 404


def test_invalid_writes_leave_device_unchanged(client: TestClient) -> None:
    owner = create_customer(client)
    other_owner = create_customer(client)
    device = create_device(client, owner)
    path = f"{DEVICES}/{device['id']}"
    payload = {"customer_id": owner, "device_type": "Laptop"}
    for invalid in [
        {"device_type": "Laptop"},
        {"customer_id": owner},
        payload | {"id": 1},
        payload | {"unknown": "x"},
        payload | {"customer_id": True},
        payload | {"customer_id": 0},
        payload | {"customer_id": MAX_ID + 1},
    ]:
        assert client.post(DEVICES, json=invalid).status_code == 422
    for invalid in [
        {"customer_id": owner},
        {"customer_id": other_owner, "model": "Changed"},
        {"id": device["id"]},
        {"unknown": "x"},
        {"device_type": None},
        {"device_type": " \t "},
        {"device_type": "x" * 51},
        {"brand": "x" * 81},
        {"model": "x" * 121},
        {"serial_number": "x" * 121},
    ]:
        assert client.patch(path, json=invalid).status_code == 422
    for field in ["device_type", "brand", "model", "serial_number"]:
        assert client.patch(path, json={field: "x\0y"}).status_code == 422
    assert client.get(path).json() == device


def test_invalid_path_and_list_parameters(client: TestClient) -> None:
    for invalid_id in [0, -1, MAX_ID + 1, "abc"]:
        path = f"{DEVICES}/{invalid_id}"
        assert client.get(path).status_code == 422
        assert client.patch(path, json={}).status_code == 422
        assert (
            client.get(DEVICES, params={"customer_id": invalid_id}).status_code == 422
        )
    for params in [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"offset": MAX_ID + 1},
        {"unknown": 1},
    ]:
        assert client.get(DEVICES, params=params).status_code == 422
