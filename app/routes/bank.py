from datetime import datetime
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, selectinload
from pydantic import BaseModel
from typing import Optional, List

from app.config import settings
from app.extensions import get_db
from app.models.user import User
from app.models.country import Country
from app.models.bank_account import BankAccount
from app.models.bank_connection import BankConnection
from app.models.bank_provider import BankProvider
from app.schemas.bank import (
    BankAccountVerificationRequest,
    BankDisconnectRequest,
    BankConnectRequest,
    BankTokenExchangeRequest, BankAccountResponse,
)
from app.providers.flutterwave_provider import FlutterwaveProvider
from app.providers.mono_provider import MonoProvider
from app.providers.paystack_provider import PaystackProvider
from app.providers.plaid_provider import PlaidProvider
from app.providers import (
    IMPLEMENTED_BANKING_PROVIDERS,
    get_providers_for_country,
    provider_metadata,
)
from app.utils.auth import get_current_user
from app.utils.i18n import t, user_language
from app.middleware.activity import log_activity

router = APIRouter(prefix="/bank", tags=["banking"])




def get_user_country(db: Session, current_user: User):
    if not current_user.country_id:
        return None
    return db.get(Country, current_user.country_id)


def provider_payload(code: str, name: Optional[str] = None, features: Optional[List[str]] = None):
    metadata = provider_metadata(code)
    normalized_code = metadata["code"]
    return {
        "code": normalized_code,
        "name": name or metadata["name"],
        "features": features or metadata["features"],
    }


def provider_is_configured(code: str, config: Optional[dict] = None) -> bool:
    config = config or {}
    checks = {
        "flutterwave": settings.FLUTTERWAVE_ENABLED
        and bool(config.get("secret_key") or settings.FLUTTERWAVE_SECRET_KEY),
        "paystack": settings.PAYSTACK_ENABLED
        and bool(config.get("secret_key") or settings.PAYSTACK_SECRET_KEY),
        "mono": settings.MONO_ENABLED
        and bool(config.get("secret_key") or settings.MONO_SECRET_KEY),
        "plaid": bool(
            (config.get("client_id") or settings.PLAID_CLIENT_ID)
            and (config.get("secret") or settings.PLAID_SECRET)
        ),
    }
    return checks.get(code.lower(), False)


def get_or_create_provider(
    db: Session,
    code: str,
    name: str,
    country_code: Optional[str] = None,
):
    normalized_code = code.lower()
    if normalized_code not in IMPLEMENTED_BANKING_PROVIDERS:
        raise HTTPException(400, f"Unsupported banking provider '{normalized_code}'")

    provider = db.query(BankProvider).filter_by(api_name=normalized_code).first()
    if not provider_is_configured(normalized_code, provider.api_config if provider else None):
        raise HTTPException(503, f"{provider_metadata(normalized_code)['name']} is not configured")
    if provider:
        return provider

    provider = BankProvider(
        name=name,
        api_name=normalized_code,
        country_codes=country_code or "",
        is_active=True,
        api_config={},
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


def get_provider_instance(provider: BankProvider, default_currency: str = "USD"):
    config = provider.api_config or {}
    config = {**config, "default_currency": default_currency}
    api_name = provider.api_name.lower()

    if api_name == "plaid":
        return PlaidProvider({
            **config,
            "name": provider.name,
            "api_name": provider.api_name,
            "client_id": config.get("client_id") or settings.PLAID_CLIENT_ID,
            "secret": config.get("secret") or settings.PLAID_SECRET,
            "environment": config.get("environment") or settings.PLAID_ENV,
        })
    if api_name == "flutterwave":
        return FlutterwaveProvider({
            **config,
            "name": provider.name,
            "api_name": provider.api_name,
            "enabled": settings.FLUTTERWAVE_ENABLED,
            "secret_key": config.get("secret_key") or settings.FLUTTERWAVE_SECRET_KEY,
            "public_key": config.get("public_key") or settings.FLUTTERWAVE_PUBLIC_KEY,
            "encryption_key": config.get("encryption_key") or settings.FLUTTERWAVE_ENCRYPTION_KEY,
            "base_url": config.get("base_url") or settings.FLUTTERWAVE_BASE_URL,
        })
    if api_name == "paystack":
        return PaystackProvider({
            **config,
            "name": provider.name,
            "api_name": provider.api_name,
            "secret_key": config.get("secret_key") or settings.PAYSTACK_SECRET_KEY,
            "public_key": config.get("public_key") or settings.PAYSTACK_PUBLIC_KEY,
            "base_url": config.get("base_url") or settings.PAYSTACK_BASE_URL,
        })
    if api_name == "mono":
        return MonoProvider({
            **config,
            "name": provider.name,
            "api_name": provider.api_name,
            "secret_key": config.get("secret_key") or settings.MONO_SECRET_KEY,
            "public_key": config.get("public_key") or settings.MONO_PUBLIC_KEY,
            "base_url": config.get("base_url") or settings.MONO_BASE_URL,
        })

    raise HTTPException(400, f"Unsupported banking provider '{api_name}'")


def user_country_code(db: Session, current_user: User) -> str:
    country = get_user_country(db, current_user)
    if not country or not country.code:
        raise HTTPException(400, "Select your banking country before connecting a bank")
    return country.code


def user_default_currency(db: Session, current_user: User) -> str:
    country = get_user_country(db, current_user)
    return (
        country.currency
        if country and country.currency
        else (current_user.preferences or {}).get("currency", "USD")
    )


def account_balance(account_data: dict, key: str, default: float = 0.0):
    balances = account_data.get("balances") or {}
    value = balances.get(key, default)
    return float(value or default)


def upsert_provider_accounts(
    db: Session,
    current_user: User,
    connection: BankConnection,
    accounts_data: List[dict],
):
    synced_accounts = []

    for account_data in accounts_data:
        provider_account_id = account_data.get("account_id") or account_data.get("id")
        if not provider_account_id:
            continue

        existing_account = (
            db.query(BankAccount)
            .filter_by(user_id=current_user.id, account_id=provider_account_id)
            .first()
        )
        institution = (
            account_data.get("institution", {}).get("name")
            or account_data.get("institution_name")
            or account_data.get("official_name")
            or connection.institution_name
        )
        account_name = account_data.get("name") or account_data.get("account_name") or "Bank Account"
        balances = account_data.get("balances") or {}

        if existing_account:
            existing_account.connection_id = connection.id
            existing_account.institution_name = institution
            existing_account.account_name = account_name
            existing_account.official_name = account_data.get("official_name")
            existing_account.name = account_name
            existing_account.account_type = str(account_data.get("type") or "checking")
            existing_account.type = str(account_data.get("type") or "checking")
            existing_account.subtype = str(account_data.get("subtype") or "")
            existing_account.balance_available = account_balance(account_data, "available")
            existing_account.balance_current = account_balance(account_data, "current")
            existing_account.balance_limit = balances.get("limit")
            existing_account.currency = balances.get("currency") or account_data.get("currency") or "USD"
            existing_account.is_active = True
            existing_account.last_updated = datetime.utcnow()
            synced_accounts.append(existing_account)
            continue

        account = BankAccount(
            user_id=current_user.id,
            connection_id=connection.id,
            institution_name=institution,
            account_name=account_name,
            official_name=account_data.get("official_name"),
            name=account_name,
            account_type=str(account_data.get("type") or "checking"),
            type=str(account_data.get("type") or "checking"),
            subtype=str(account_data.get("subtype") or ""),
            account_id=provider_account_id,
            balance_available=account_balance(account_data, "available"),
            balance_current=account_balance(account_data, "current"),
            balance_limit=balances.get("limit"),
            currency=balances.get("currency") or account_data.get("currency") or "USD",
            is_active=True,
        )
        db.add(account)
        synced_accounts.append(account)

    db.commit()
    for account in synced_accounts:
        db.refresh(account)

    return synced_accounts


def serialize_connection(connection: BankConnection):
    provider = connection.provider
    accounts = [account for account in connection.accounts if account.is_active]
    return {
        "id": connection.id,
        "provider": provider.api_name if provider else "unknown",
        "provider_name": provider.name if provider else "Unknown",
        "institution_name": connection.institution_name,
        "bankName": connection.institution_name,
        "account_name": accounts[0].account_name if accounts else connection.institution_name,
        "accountMask": str(accounts[0].account_id)[-4:] if accounts else None,
        "account_count": len(accounts),
        "status": "active" if connection.is_active else "disconnected",
        "last_sync": connection.last_sync.isoformat() if connection.last_sync else None,
        "created_at": connection.created_at.isoformat() if connection.created_at else None,
    }


def serialize_account(account: BankAccount):
    return {
        "id": account.id,
        "connection_id": account.connection_id,
        "institution_name": account.institution_name or "Unknown",
        "bankName": account.institution_name or "Unknown",
        "account_name": account.account_name or account.name or "Unknown",
        "account_type": account.account_type or account.type or "checking",
        "accountMask": str(account.account_id)[-4:] if account.account_id else None,
        "balance_available": account.balance_available,
        "balance_current": account.balance_current,
        "currency": account.currency or "USD",
        "status": "active" if account.is_active else "disconnected",
    }


def verification_account_id(provider_name: str, account_bank: str, account_number: str):
    fingerprint = hashlib.sha256(
        f"{provider_name}:{account_bank}:{account_number}".encode("utf-8")
    ).hexdigest()[:24]
    return f"{provider_name}-{fingerprint}"


@router.get("/providers")
def get_providers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available banking providers for user's country"""
    country = get_user_country(db, current_user)
    country_code = country.code if country else None
    candidate_codes = (
        get_providers_for_country(country_code)
        if country_code
        else sorted(IMPLEMENTED_BANKING_PROVIDERS)
    )
    configured_rows = {
        provider.api_name.lower(): provider
        for provider in db.query(BankProvider)
        .filter(BankProvider.is_active.is_(True), BankProvider.api_name.in_(candidate_codes))
        .all()
    }
    providers = []
    for code in candidate_codes:
        row = configured_rows.get(code)
        if provider_is_configured(code, row.api_config if row else None):
            providers.append(provider_payload(code, row.name if row else None))

    return {
        "country": (
            {"code": country.code, "name": country.name, "currency": country.currency}
            if country
            else None
        ),
        "providers": providers,
    }


@router.get("/accounts", response_model=List[BankAccountResponse])
def get_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's connected bank accounts"""
    accounts = (
        db.query(BankAccount)
        .filter_by(user_id=current_user.id, is_active=True)
        .all()
    )

    return [serialize_account(a) for a in accounts]


@router.get("/flutterwave/banks")
def get_flutterwave_banks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return Flutterwave's cached bank directory for the user's country."""
    country_code = user_country_code(db, current_user)
    provider = get_or_create_provider(db, "flutterwave", "Flutterwave", country_code)
    try:
        banks = get_provider_instance(provider).list_banks(country_code)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"country": country_code, "banks": banks}


@router.get("/connections")
def get_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's bank connections"""
    connections = (
        db.query(BankConnection)
        .options(selectinload(BankConnection.provider), selectinload(BankConnection.accounts))
        .filter_by(user_id=current_user.id, is_active=True)
        .all()
    )

    return [serialize_connection(c) for c in connections]

@router.post("/connect")
def connect_bank(
    data: BankConnectRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a live bank connection. OAuth providers return link/auth data."""
    country_code = user_country_code(db, current_user)
    provider = get_or_create_provider(db, data.bank_code, data.bank_name, country_code)
    provider_client = get_provider_instance(provider, user_default_currency(db, current_user))
    link_data = provider_client.create_link_token(
        str(current_user.id),
        country_code,
    )

    if link_data.get("error"):
        raise HTTPException(400, link_data["error"])

    log_activity(db,
        request,
        current_user.id,
        "bank_connection_start",
        entity_type="bank_connection",
        description=f"Started bank connection for {provider.name}",
        metadata={"provider": provider.api_name},
    )

    return {
        "provider": provider.api_name,
        "provider_name": provider.name,
        "requires_exchange": provider.api_name in {"plaid", "mono", "flutterwave"},
        **link_data,
    }


@router.post("/exchange-token")
def exchange_bank_token(
    data: BankTokenExchangeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Finish a live bank connection and sync accounts from the provider."""
    country_code = user_country_code(db, current_user)
    provider = get_or_create_provider(db, data.bank_code, data.bank_name, country_code)
    provider_client = get_provider_instance(provider, user_default_currency(db, current_user))
    token_data = provider_client.exchange_token(data.public_token, data.metadata)

    if token_data.get("error") or token_data.get("success") is False:
        raise HTTPException(400, token_data.get("error") or "Token exchange failed")

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(400, "Provider did not return an access token")

    institution_name = (
        data.metadata.get("institution", {}).get("name")
        or data.metadata.get("institution_name")
        or data.bank_name
    )

    connection = (
        db.query(BankConnection)
        .filter_by(user_id=current_user.id, provider_id=provider.id, is_active=True)
        .first()
    )
    if not connection:
        connection = BankConnection(
            user_id=current_user.id,
            provider_id=provider.id,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db.add(connection)

    connection.access_token = access_token
    connection.item_id = token_data.get("item_id")
    connection.institution_id = (
        data.metadata.get("institution", {}).get("institution_id")
        or data.metadata.get("institution_id")
    )
    connection.institution_name = institution_name
    connection.last_sync = datetime.utcnow()
    db.commit()
    db.refresh(connection)

    accounts_data = provider_client.get_accounts(access_token)
    upsert_provider_accounts(db, current_user, connection, accounts_data)
    db.refresh(connection)
    log_activity(db,
        request,
        current_user.id,
        "bank_connection_complete",
        entity_type="bank_connection",
        entity_id=connection.id,
        description=f"Connected {connection.institution_name}",
        metadata={"provider": provider.api_name, "accounts": len(accounts_data or [])},
    )

    return serialize_connection(connection)

@router.post("/verify-account")
def verify_bank_account(
    data: BankAccountVerificationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify a bank account with providers that use account resolution."""
    country = get_user_country(db, current_user)
    country_code = country.code if country and country.code else user_country_code(db, current_user)
    provider = get_or_create_provider(db, data.bank_code, data.bank_name, country_code)
    provider_client = get_provider_instance(provider, user_default_currency(db, current_user))

    if not hasattr(provider_client, "verify_bank_account"):
        raise HTTPException(400, f"{provider.name} does not support account verification")

    institution_name = data.bank_name
    if provider.api_name.lower() == "flutterwave":
        try:
            supported_banks = provider_client.list_banks(country_code)
        except RuntimeError as exc:
            raise HTTPException(503, str(exc)) from exc
        selected_bank = next(
            (bank for bank in supported_banks if bank["code"] == data.account_bank),
            None,
        )
        if not selected_bank:
            raise HTTPException(400, "Select a supported bank")
        institution_name = selected_bank["name"]

    verification = provider_client.verify_bank_account(
        data.account_number,
        data.account_bank,
        country_code,
    )

    if verification.get("error") or verification.get("success") is False:
        raise HTTPException(400, verification.get("error") or "Account verification failed")

    account_number = str(verification.get("account_number") or data.account_number)
    account_name = verification.get("account_name") or "Verified bank account"
    currency = (
        country.currency
        if country and country.currency
        else (current_user.preferences or {}).get("currency", "USD")
    )

    connection = (
        db.query(BankConnection)
        .filter_by(
            user_id=current_user.id,
            provider_id=provider.id,
            institution_id=data.account_bank,
            is_active=True,
        )
        .first()
    )
    if not connection:
        connection = BankConnection(
            user_id=current_user.id,
            provider_id=provider.id,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db.add(connection)

    connection.institution_id = data.account_bank
    connection.institution_name = institution_name
    connection.last_sync = datetime.utcnow()
    db.commit()
    db.refresh(connection)

    provider_account_id = verification_account_id(provider.api_name, data.account_bank, account_number)
    account = (
        db.query(BankAccount)
        .filter_by(user_id=current_user.id, account_id=provider_account_id)
        .first()
    )
    if not account:
        account = BankAccount(
            user_id=current_user.id,
            account_id=provider_account_id,
            created_at=datetime.utcnow(),
        )
        db.add(account)

    account.connection_id = connection.id
    account.institution_name = institution_name
    account.account_name = account_name
    account.official_name = account_name
    account.name = account_name
    account.account_type = "checking"
    account.type = "bank_account"
    account.subtype = "verified"
    account.balance_available = 0.0
    account.balance_current = 0.0
    account.currency = currency
    account.is_active = True
    account.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(connection)
    log_activity(db,
        request,
        current_user.id,
        "bank_connection_complete",
        entity_type="bank_connection",
        entity_id=connection.id,
        description=f"Verified and connected {institution_name}",
        metadata={"provider": provider.api_name},
    )

    return serialize_connection(connection)

@router.post("/disconnect")
def disconnect_bank(
    data: BankDisconnectRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect a bank account"""
    connection = db.query(BankConnection).filter_by(
        id=data.id, user_id=current_user.id
    ).first()
    if not connection:
        raise HTTPException(404, "Connection not found")
    connection.is_active = False
    for account in connection.accounts:
        account.is_active = False
    db.commit()
    log_activity(db,
        request,
        current_user.id,
        "bank_disconnect",
        entity_type="bank_connection",
        entity_id=connection.id,
        description=f"Disconnected {connection.institution_name}",
    )
    return {"message": t("bank_disconnected", lang=user_language(current_user))}


@router.post("/connections/{connection_id}/sync")
def sync_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync connected bank accounts from the live provider."""
    connection = db.query(BankConnection).filter_by(
        id=connection_id, user_id=current_user.id, is_active=True
    ).first()
    if not connection:
        raise HTTPException(404, "Connection not found")
    if not connection.access_token:
        connection.last_sync = datetime.utcnow()
        for account in connection.accounts:
            account.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(connection)
        return serialize_connection(connection)

    provider_client = get_provider_instance(connection.provider, user_default_currency(db, current_user))
    accounts_data = provider_client.get_accounts(connection.access_token)
    upsert_provider_accounts(db, current_user, connection, accounts_data)
    connection.last_sync = datetime.utcnow()
    db.commit()
    db.refresh(connection)
    return serialize_connection(connection)


# app/routes/bank.py - add this
@router.post("/providers/{provider_name}/test")
def test_provider(
        provider_name: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Test a banking provider connection"""
    from app.providers.flutterwave_provider import FlutterwaveProvider
    from app.providers.paystack_provider import PaystackProvider
    from app.providers.plaid_provider import PlaidProvider

    providers = {
        "flutterwave": FlutterwaveProvider,
        "paystack": PaystackProvider,
        "plaid": PlaidProvider,
    }

    if provider_name not in providers:
        raise HTTPException(404, f"Provider '{provider_name}' not found")

    try:
        provider_class = providers[provider_name]
        config = {
            "flutterwave": {
                "secret_key": settings.FLUTTERWAVE_SECRET_KEY,
                "public_key": settings.FLUTTERWAVE_PUBLIC_KEY,
                "base_url": settings.FLUTTERWAVE_BASE_URL,
            },
            "paystack": {
                "secret_key": settings.PAYSTACK_SECRET_KEY,
                "public_key": settings.PAYSTACK_PUBLIC_KEY,
                "base_url": settings.PAYSTACK_BASE_URL,
            },
            "plaid": {
                "client_id": settings.PLAID_CLIENT_ID,
                "secret": settings.PLAID_SECRET,
                "environment": settings.PLAID_ENV,
            },
        }.get(provider_name, {})

        provider = provider_class(config)
        health = provider.health_check() if hasattr(provider, 'health_check') else {"status": "unknown"}

        return {"provider": provider_name, "health": health}
    except Exception as e:
        return {"provider": provider_name, "status": "error", "error": str(e)}
