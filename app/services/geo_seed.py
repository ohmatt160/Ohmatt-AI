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


def upsert_models(model, values_list: list[dict]) -> int:
    existing = {
        record.code: record
        for record in db_session.query(model)
        .filter(model.code.in_([values["code"] for values in values_list]))
        .all()
    }
    changed_count = 0
    for values in values_list:
        record = existing.get(values["code"])
        if not record:
            db_session.add(model(**values))
            changed_count += 1
            continue
        changed = False
        for key, value in values.items():
            if getattr(record, key) != value:
                setattr(record, key, value)
                changed = True
        changed_count += int(changed)
    return changed_count


def seed_geo_data() -> dict:
    created_or_updated = {
        "continents": 0,
        "countries": 0,
        "languages": 0,
    }

    created_or_updated["continents"] = upsert_models(Continent, CONTINENTS)
    created_or_updated["languages"] = upsert_models(Language, LANGUAGES)
    created_or_updated["countries"] = upsert_models(Country, COUNTRIES)

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
