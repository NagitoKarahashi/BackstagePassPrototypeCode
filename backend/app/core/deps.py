import os
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import ExpiredSignatureError, InvalidAudienceError, InvalidSignatureError, InvalidTokenError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from app.db.supabase_client import get_supabase_client

bearer_scheme = HTTPBearer(auto_error=False)


def supabase_dep() -> Client:
    return get_supabase_client()


@dataclass
class CurrentUser:
    id: str
    privy_id: str
    email: str | None = None
    wallet_address: str | None = None
    claims: dict[str, Any] | None = None
    user_metadata: dict[str, Any] | None = None


def current_user_dep(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    sb: Client = Depends(supabase_dep),
) -> Any:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token")

    privy_app_id = os.getenv("PRIVY_APP_ID")
    privy_verification_key = os.getenv("PRIVY_VERIFICATION_KEY")

    if not privy_app_id or not privy_verification_key:
        raise HTTPException(status_code=500, detail="Privy auth is not configured on backend")

    try:
        claims = jwt.decode(
            token,
            privy_verification_key,
            algorithms=["ES256"],
            audience=privy_app_id,
            issuer="privy.io",
        )
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Privy token expired")
    except InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Privy token audience mismatch")
    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Privy token signature invalid")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Privy token invalid")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Privy token decode error: {str(e)}")

    privy_id = claims.get("sub")
    if not privy_id:
        raise HTTPException(status_code=401, detail="Privy token missing subject")

    # Privy access token里不一定直接有 email / wallet_address
    # 先尽量读，读不到就留空，不阻塞基础 profile 流程
    email = claims.get("email")
    wallet_address = claims.get("wallet_address")

    return CurrentUser(
        id=privy_id,
        privy_id=privy_id,
        email=email,
        wallet_address=wallet_address,
        claims=claims,
        user_metadata={},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    sb: Client = Depends(supabase_dep),
) -> Any:
    return current_user_dep(credentials, sb)