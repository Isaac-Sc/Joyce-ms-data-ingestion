
import hmac
import hashlib
import time
from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel
from database import database, devices, inventory
from datetime import datetime

app = FastAPI()

class IngestionData(BaseModel):
    serial_number: str
    payload: dict

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

async def verify_signature(request: Request, serial_number: str, x_signature: str = Header(...)):
    """
    Verifies the HMAC-SHA256 signature of the request.
    The signature is calculated from the request body and a timestamp.
    """
    body = await request.body()
    timestamp = request.headers.get("X-Timestamp")
    if not timestamp:
        raise HTTPException(status_code=400, detail="X-Timestamp header is missing")

    # Fetch the device's secret from the database
    query = inventory.select().where(inventory.c.serial_number == serial_number)
    device_inventory = await database.fetch_one(query)
    if not device_inventory:
        raise HTTPException(status_code=404, detail="Device not found in inventory")
    
    device_secret = device_inventory["device_secret"]

    # Calculate the expected signature
    message = body + timestamp.encode()
    expected_signature = hmac.new(
        device_secret.encode(),
        message,
        hashlib.sha256
    ).hexdigest()

    # Compare the expected signature with the provided signature
    if not hmac.compare_digest(expected_signature, x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

@app.post("/ingest")
async def ingest_data(request: Request, data: IngestionData, x_signature: str = Header(...)):
    """
    Ingests data from a device.
    Verifies the HMAC signature, checks if the device is not expired,
    and updates the last_seen_at timestamp.
    """
    await verify_signature(request, data.serial_number, x_signature)
    
    # Check if the device is expired
    query = devices.select().where(devices.c.serial_number == data.serial_number)
    device = await database.fetch_one(query)

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if device["prepaid_expiry"] and device["prepaid_expiry"] < datetime.utcnow():
        # Here you would also check for an active subscription
        # For now, we'll just deny service if the prepaid period is over
        raise HTTPException(status_code=403, detail="Device subscription has expired")

    # Update the last_seen_at timestamp
    update_query = (
        devices.update()
        .where(devices.c.serial_number == data.serial_number)
        .values(last_seen_at=datetime.utcnow())
    )
    await database.execute(update_query)

    return {"message": "Data ingested successfully"}
