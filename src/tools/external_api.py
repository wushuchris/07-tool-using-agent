from typing import Any, Dict, List

import requests


BASE_URL = "https://api.worldbank.org/v2/country"


def lookup_country(country_name: str) -> Dict[str, Any]:
    """
    Retrieve basic country information from the World Bank Countries API.

    This tool demonstrates controlled access to an external HTTP API
    without requiring an API key.
    """

    if not isinstance(country_name, str):
        raise TypeError("country_name must be a string.")

    country_name = country_name.strip()

    if not country_name:
        raise ValueError("country_name cannot be empty.")

    if len(country_name) > 100:
        raise ValueError("country_name is too long.")

    try:
        response = requests.get(
            BASE_URL,
            params={
                "format": "json",
                "per_page": 400,
            },
            timeout=10,
        )

        response.raise_for_status()

    except requests.Timeout as exc:
        raise RuntimeError(
            "World Bank API request timed out."
        ) from exc

    except requests.RequestException as exc:
        raise RuntimeError(
            f"World Bank API request failed: {exc}"
        ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "World Bank API returned invalid JSON."
        ) from exc

    if (
        not isinstance(payload, list)
        or len(payload) < 2
        or not isinstance(payload[1], list)
    ):
        raise RuntimeError(
            "World Bank API returned an unexpected response."
        )

    countries: List[Dict[str, Any]] = payload[1]

    normalized_query = country_name.casefold()

    exact_matches = [
        country
        for country in countries
        if country.get("name", "").casefold() == normalized_query
    ]

    if exact_matches:
        country = exact_matches[0]
    else:
        partial_matches = [
            country
            for country in countries
            if normalized_query in country.get("name", "").casefold()
        ]

        if len(partial_matches) == 1:
            country = partial_matches[0]
        elif len(partial_matches) > 1:
            names = [
                match.get("name")
                for match in partial_matches[:10]
            ]

            raise ValueError(
                f"Country name '{country_name}' is ambiguous. "
                f"Possible matches: {names}"
            )
        else:
            raise ValueError(
                f"No country found matching '{country_name}'."
            )

    region = country.get("region") or {}
    income_level = country.get("incomeLevel") or {}
    lending_type = country.get("lendingType") or {}

    return {
        "query": country_name,
        "name": country.get("name"),
        "iso2_code": country.get("iso2Code"),
        "iso3_code": country.get("id"),
        "capital": country.get("capitalCity"),
        "region": region.get("value"),
        "income_level": income_level.get("value"),
        "lending_type": lending_type.get("value"),
        "longitude": country.get("longitude"),
        "latitude": country.get("latitude"),
    }