from app.extensions import db_session
from app.models.continent import Continent
from app.models.country import Country
from app.models.language import Language


CONTINENTS = [
    {"code": "AF", "name": "Africa"},
    {"code": "AN", "name": "Antarctica"},
    {"code": "AS", "name": "Asia"},
    {"code": "EU", "name": "Europe"},
    {"code": "NA", "name": "North America"},
    {"code": "OC", "name": "Oceania"},
    {"code": "SA", "name": "South America"},
]

COUNTRIES = [
    {"code": "NG", "name": "Nigeria", "continent": "AF", "currency": "NGN", "timezone": "Africa/Lagos", "language": "en", "other_provider": "mono"},
    {"code": "GH", "name": "Ghana", "continent": "AF", "currency": "GHS", "timezone": "Africa/Accra", "language": "en", "other_provider": "paystack"},
    {"code": "KE", "name": "Kenya", "continent": "AF", "currency": "KES", "timezone": "Africa/Nairobi", "language": "en", "other_provider": "flutterwave"},
    {"code": "TZ", "name": "Tanzania", "continent": "AF", "currency": "TZS", "timezone": "Africa/Dar_es_Salaam", "language": "sw", "other_provider": "mpesa"},
    {"code": "UG", "name": "Uganda", "continent": "AF", "currency": "UGX", "timezone": "Africa/Kampala", "language": "en", "other_provider": "mpesa"},
    {"code": "RW", "name": "Rwanda", "continent": "AF", "currency": "RWF", "timezone": "Africa/Kigali", "language": "en", "other_provider": "flutterwave"},
    {"code": "ZA", "name": "South Africa", "continent": "AF", "currency": "ZAR", "timezone": "Africa/Johannesburg", "language": "en", "other_provider": "flutterwave"},
    {"code": "EG", "name": "Egypt", "continent": "AF", "currency": "EGP", "timezone": "Africa/Cairo", "language": "ar", "other_provider": "fawry"},
    {"code": "MA", "name": "Morocco", "continent": "AF", "currency": "MAD", "timezone": "Africa/Casablanca", "language": "ar", "other_provider": "stripe"},
    {"code": "US", "name": "United States", "continent": "NA", "currency": "USD", "timezone": "America/New_York", "language": "en", "plaid_supported": True, "plaid_country_code": "US"},
    {"code": "GB", "name": "United Kingdom", "continent": "EU", "currency": "GBP", "timezone": "Europe/London", "language": "en", "plaid_supported": True, "plaid_country_code": "GB"},
    {"code": "CA", "name": "Canada", "continent": "NA", "currency": "CAD", "timezone": "America/Toronto", "language": "en", "plaid_supported": True, "plaid_country_code": "CA"},
    {"code": "FR", "name": "France", "continent": "EU", "currency": "EUR", "timezone": "Europe/Paris", "language": "fr", "other_provider": "truelayer"},
    {"code": "ES", "name": "Spain", "continent": "EU", "currency": "EUR", "timezone": "Europe/Madrid", "language": "es", "other_provider": "truelayer"},
    {"code": "PT", "name": "Portugal", "continent": "EU", "currency": "EUR", "timezone": "Europe/Lisbon", "language": "pt", "other_provider": "truelayer"},
    {"code": "BR", "name": "Brazil", "continent": "SA", "currency": "BRL", "timezone": "America/Sao_Paulo", "language": "pt", "other_provider": "stripe"},
    {"code": "MX", "name": "Mexico", "continent": "NA", "currency": "MXN", "timezone": "America/Mexico_City", "language": "es", "other_provider": "stripe"},
]

LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "fr", "name": "French", "native_name": "Français"},
    {"code": "es", "name": "Spanish", "native_name": "Español"},
    {"code": "ar", "name": "Arabic", "native_name": "العربية"},
    {"code": "pt", "name": "Portuguese", "native_name": "Português"},
    {"code": "sw", "name": "Swahili", "native_name": "Kiswahili"},
    {"code": "ha", "name": "Hausa", "native_name": "Hausa"},
    {"code": "yo", "name": "Yoruba", "native_name": "Yorùbá"},
    {"code": "ig", "name": "Igbo", "native_name": "Igbo"},
]


def upsert_model(model, lookup: dict, values: dict) -> bool:
    record = db_session.query(model).filter_by(**lookup).first()
    if not record:
        db_session.add(model(**values))
        return True

    changed = False
    for key, value in values.items():
        if getattr(record, key) != value:
            setattr(record, key, value)
            changed = True
    return changed


def seed_geo_data() -> dict:
    created_or_updated = {
        "continents": 0,
        "countries": 0,
        "languages": 0,
    }

    for continent in CONTINENTS:
        if upsert_model(Continent, {"code": continent["code"]}, continent):
            created_or_updated["continents"] += 1

    for language in LANGUAGES:
        if upsert_model(Language, {"code": language["code"]}, language):
            created_or_updated["languages"] += 1

    for country in COUNTRIES:
        if upsert_model(Country, {"code": country["code"]}, country):
            created_or_updated["countries"] += 1

    db_session.commit()

    return {
        "success": True,
        "seeded": created_or_updated,
        "totals": {
            "continents": len(CONTINENTS),
            "countries": len(COUNTRIES),
            "languages": len(LANGUAGES),
        },
    }
