import pytest

import src.tools.database as database_tool
import src.tools.external_api as external_api_tool
from src.tools.calculator import calculator


def test_calculator_basic_math():
    result = calculator("25 * 8")

    assert result["expression"] == "25 * 8"
    assert result["result"] == 200


def test_calculator_respects_operator_precedence():
    result = calculator("10 + 5 * 2")

    assert result["result"] == 20


def test_calculator_rejects_code_execution():
    with pytest.raises(ValueError):
        calculator(
            "__import__('os').system('echo hacked')"
        )


def test_calculator_rejects_division_by_zero():
    with pytest.raises(
        ValueError,
        match="Division by zero",
    ):
        calculator("10 / 0")


def test_inventory_category_search(
    tmp_path,
    monkeypatch,
):
    test_db = tmp_path / "operations.db"

    monkeypatch.setattr(
        database_tool,
        "DB_PATH",
        test_db,
    )

    result = database_tool.search_inventory(
        category="Electronics"
    )

    assert result["count"] == 3

    names = {
        item["item_name"]
        for item in result["items"]
    }

    assert names == {
        "Laptop",
        "Monitor",
        "Keyboard",
    }


def test_inventory_item_search(
    tmp_path,
    monkeypatch,
):
    test_db = tmp_path / "operations.db"

    monkeypatch.setattr(
        database_tool,
        "DB_PATH",
        test_db,
    )

    result = database_tool.search_inventory(
        item_name="chair"
    )

    assert result["count"] == 1
    assert (
        result["items"][0]["item_name"]
        == "Office Chair"
    )


class FakeResponse:
    def __init__(
        self,
        payload,
        status_code=200,
    ):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _world_bank_payload():
    return [
        {
            "page": 1,
            "pages": 1,
            "total": 1,
        },
        [
            {
                "id": "JPN",
                "iso2Code": "JP",
                "name": "Japan",
                "region": {
                    "value": "East Asia & Pacific"
                },
                "incomeLevel": {
                    "value": "High income"
                },
                "lendingType": {
                    "value": "Not classified"
                },
                "capitalCity": "Tokyo",
                "longitude": "139.77",
                "latitude": "35.67",
            }
        ],
    ]


def test_country_lookup_success(
    monkeypatch,
):
    def fake_get(*args, **kwargs):
        return FakeResponse(
            _world_bank_payload()
        )

    monkeypatch.setattr(
        external_api_tool.requests,
        "get",
        fake_get,
    )

    result = external_api_tool.lookup_country(
        "Japan"
    )

    assert result["name"] == "Japan"
    assert result["iso2_code"] == "JP"
    assert result["iso3_code"] == "JPN"
    assert result["capital"] == "Tokyo"
    assert (
        result["region"]
        == "East Asia & Pacific"
    )
    assert (
        result["income_level"]
        == "High income"
    )


def test_country_lookup_not_found(
    monkeypatch,
):
    def fake_get(*args, **kwargs):
        return FakeResponse(
            [
                {
                    "page": 1,
                    "pages": 1,
                    "total": 0,
                },
                [],
            ]
        )

    monkeypatch.setattr(
        external_api_tool.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        ValueError,
        match="No country found",
    ):
        external_api_tool.lookup_country(
            "DefinitelyNotARealCountryXYZ"
        )