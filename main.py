from fastapi import FastAPI
from datetime import date, datetime

# how we define the app
app = FastAPI()

# declaration of the root endpoint
@app.get("/")
async def root():
    return{"message": "Hello World"}

@app.get("/campaigns")
async def campaigns(
    campaign_id: int,
    name: str,
    due_date: date,
    created_at: datetime,
    updated_at: datetime,
    status: str,
):
    return {
        "campaign_id": campaign_id,
        "name": name,
        "due_date": due_date,
        "created_at": created_at,
        "updated_at": updated_at,
        "status": status,
    }