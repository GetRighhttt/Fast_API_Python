from datetime import datetime
from random import randint
from typing import Any

from fastapi import FastAPI, HTTPException

# how we define the app
app = FastAPI(root_path="/api/v1")


# declaration of the root endpoint
@app.get("/")
async def root():
    return {"message": "Root endpoint of the API"}


dateFormatter = datetime.now().isoformat(timespec="hours").replace(":", "-")
campaigns_list: Any = [
    {
        "campaign_id": 1,
        "name": "Emerald Coast",
        "due_date": dateFormatter,
        "created_at": dateFormatter,
    },
    {
        "campaign_id": 2,
        "name": "Be the Magic",
        "due_date": dateFormatter,
        "created_at": dateFormatter,
    },
    {
        "campaign_id": 3,
        "name": "Wizard of Emerald",
        "due_date": dateFormatter,
        "created_at": dateFormatter,
    },
    {
        "campaign_id": 4,
        "name": "Oz of City",
        "due_date": dateFormatter,
        "created_at": dateFormatter,
    },
]

person: Any = [
    {
        "first_name": "stefan",
        "last_name": "Bayne",
    },
    {
        "first_name": "vincentjr",
        "last_name": "bayne",
    },
    {
        "first_name": "shawn",
        "last_name": "bayne",
    },
    {
        "first_name": "vincentsr",
        "last_name": "bayne",
    }
]


@app.get("/campaigns")
async def read_campaigns():
    return {"campaigns": campaigns_list}


@app.get("/campaigns/{c_id}")
async def read_campaign_by_id(c_id: int):
    for each_campaign in campaigns_list:
        if each_campaign["campaign_id"] == c_id:
            return {"campaigns": each_campaign}
    return HTTPException(status_code=404, detail="Campaign not found")


@app.post("/campaigns")
async def create_campaign(body: dict[str, Any]):
    new: Any = {
        "campaign_id": randint(1, 100),
        "name": body["name"],
        "due_date": body.get("due_date"),
        "created_at": dateFormatter,
    }
    campaigns_list.append(new)
    return {"campaigns": new}


@app.get("/names")
async def read_names():
    return {"names": person}


@app.get("/names/{person_name}")
async def read_person_first_name(person_name: str):
    for each_name in person:
        if each_name["first_name"] == person_name:
            return {"first_name": each_name}
        elif each_name["last_name"] == person_name:
            return {"last_name": each_name}
    raise HTTPException(status_code=404, detail="Last name not found")
