# app/routes/geo.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.extensions import get_db, db_session
from app.models.country import Country
from app.models.continent import Continent
from app.models.language import Language
from app.services.geo_seed import seed_geo_data as seed_geo_records

router = APIRouter(prefix="/geo", tags=["geography"])


# ==================== Countries ====================

@router.get("/countries")
async def list_countries(
    continent: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    plaid_supported: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all countries with optional filtering"""
    query = db_session.query(Country)

    if continent:
        query = query.filter_by(continent=continent.upper())
    if language:
        query = query.filter_by(language=language.lower())
    if plaid_supported is not None:
        query = query.filter_by(plaid_supported=plaid_supported)

    countries = query.order_by(Country.name.asc()).all()

    return {
        "success": True,
        "count": len(countries),
        "countries": [
            {
                "code": c.code,
                "name": c.name,
                "continent": c.continent,
                "currency": c.currency,
                "timezone": c.timezone,
                "language": c.language,
                "plaid_supported": c.plaid_supported,
                "other_provider": c.other_provider,
            }
            for c in countries
        ],
    }


@router.get("/countries/{country_code}")
async def get_country(country_code: str, db: Session = Depends(get_db)):
    """Get a specific country by code"""
    country = db_session.query(Country).filter_by(code=country_code.upper()).first()

    if not country:
        raise HTTPException(status_code=404, detail=f"Country '{country_code}' not found")

    return {
        "success": True,
        "country": {
            "code": country.code,
            "name": country.name,
            "continent": country.continent,
            "currency": country.currency,
            "timezone": country.timezone,
            "language": country.language,
            "plaid_supported": country.plaid_supported,
            "other_provider": country.other_provider,
        },
    }


@router.get("/countries/supported/banking")
async def get_banking_countries(db: Session = Depends(get_db)):
    """Get countries with banking provider support"""
    countries = (
        db_session.query(Country)
        .filter(
            (Country.plaid_supported == True) | (Country.other_provider.isnot(None))
        )
        .order_by(Country.name.asc())
        .all()
    )

    result = []
    for country in countries:
        providers = []
        if country.plaid_supported:
            providers.append("plaid")
        if country.other_provider:
            providers.append(country.other_provider)

        result.append(
            {
                "code": country.code,
                "name": country.name,
                "continent": country.continent,
                "currency": country.currency,
                "providers": providers,
            }
        )

    return {"success": True, "count": len(result), "countries": result}


# ==================== Continents ====================

@router.get("/continents")
async def list_continents(db: Session = Depends(get_db)):
    """Get all continents"""
    continents = db_session.query(Continent).order_by(Continent.name.asc()).all()

    return {
        "success": True,
        "count": len(continents),
        "continents": [{"code": c.code, "name": c.name} for c in continents],
    }


@router.get("/continents/{continent_code}/countries")
async def get_continent_countries(continent_code: str, db: Session = Depends(get_db)):
    """Get all countries in a continent"""
    continent = db_session.query(Continent).filter_by(code=continent_code.upper()).first()

    if not continent:
        raise HTTPException(status_code=404, detail=f"Continent '{continent_code}' not found")

    countries = (
        db_session.query(Country)
        .filter_by(continent=continent.code)
        .order_by(Country.name.asc())
        .all()
    )

    return {
        "success": True,
        "continent": {"code": continent.code, "name": continent.name},
        "count": len(countries),
        "countries": [
            {"code": c.code, "name": c.name, "currency": c.currency, "plaid_supported": c.plaid_supported}
            for c in countries
        ],
    }


# ==================== Languages ====================

@router.get("/languages")
async def list_languages(db: Session = Depends(get_db)):
    """Get all languages"""
    languages = db_session.query(Language).order_by(Language.name.asc()).all()

    return {
        "success": True,
        "count": len(languages),
        "languages": [
            {"code": l.code, "name": l.name, "native_name": l.native_name}
            for l in languages
        ],
    }


@router.get("/languages/{language_code}")
async def get_language(language_code: str, db: Session = Depends(get_db)):
    """Get a specific language by code"""
    language = db_session.query(Language).filter_by(code=language_code.lower()).first()

    if not language:
        raise HTTPException(status_code=404, detail=f"Language '{language_code}' not found")

    return {
        "success": True,
        "language": {
            "code": language.code,
            "name": language.name,
            "native_name": language.native_name,
        },
    }


@router.post("/seed")
async def seed_geo_data():
    """Seed countries and languages"""
    result = seed_geo_records()
    return {
        "message": "Geography data seeded",
        **result,
    }
