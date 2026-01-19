import json
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import secrets
import hashlib
from app.db.session import db_manager
from app.core.security import get_token_payload

router = APIRouter()

class PairingClaim(BaseModel):
    pairing_code: str

@router.post("/pairing/claim")
async def claim_device(
    claim: PairingClaim,
    payload: dict = Depends(get_token_payload)
):
    # 1. Redis Lookup
    # Key format: "pairing:{code}"
    pairing_key = f"pairing:{claim.pairing_code}"
    stored_data_str = await db_manager.redis.get(pairing_key)
    
    if not stored_data_str:
        raise HTTPException(status_code=404, detail="Invalid or expired pairing code")

    try:
        stored_data = json.loads(stored_data_str)
        device_id = stored_data.get("device_id")
    except json.JSONDecodeError:
        # Legacy fallback: if the value is just the device_id string
        device_id = stored_data_str

    if not device_id:
        raise HTTPException(status_code=404, detail="Invalid pairing code data")
        
    # 2. Verify User
    # Firebase JWT 'sub' claim contains the user ID
    external_auth_id = payload.get("sub")
    if not external_auth_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing subject")

    user = await db_manager.users.get_by_external_id(external_auth_id)
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")

    # 3. Generate Token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    # 4. Register Device
    # This upserts the device, linking it to the user's account
    await db_manager.devices.register_device(
        device_id=device_id, 
        account_id=user.account_id, 
        auth_token_hash=token_hash
    )

    # 5. Update Status in Redis (CLAIMED)
    # Store the apikey so the Daemon can retrieve it via the Ingestion API
    # TTL: 10 minutes (600s) buffer for the daemon to poll
    claim_data = {
        "status": "CLAIMED",
        "apikey": raw_token,
        "device_id": device_id
    }
    await db_manager.redis.set(pairing_key, json.dumps(claim_data), ex=600)

    return {"status": "success", "device_id": device_id}
