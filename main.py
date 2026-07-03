from datetime import datetime
from random import randint
from typing import Any

from fastapi import FastAPI, HTTPException
from starlette.responses import Response

# how we define the app
app = FastAPI(root_path="/api/v1")


# declaration of the root endpoint
@app.get("/")
async def root():
    return {"message": "Root endpoint of the API"}


campaigns_list: Any = [
    {
        "campaign_id": 1,
        "name": "Emerald Coast",
        "due_date": datetime.now(),
        "created_at": datetime.now().strftime("%B %d, %Y %I:%M %p"),
    },
    {
        "campaign_id": 2,
        "name": "Be the Magic",
        "due_date": datetime.now().strftime("%B %d, %Y %I:%M %p"),
        "created_at": datetime.now().strftime("%B %d, %Y %I:%M %p"),
    },
    {
        "campaign_id": 3,
        "name": "Wizard of Emerald",
        "due_date": datetime.now().strftime("%B %d, %Y %I:%M %p"),
        "created_at": datetime.now().strftime("%B %d, %Y %I:%M %p"),
    },
    {
        "campaign_id": 4,
        "name": "Oz of City",
        "due_date": datetime.now().strftime("%B %d, %Y %I:%M %p"),
        "created_at": datetime.now().strftime("%B %d, %Y %I:%M %p"),
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


@app.get("/campaigns", status_code=200)
async def read_campaigns():
    return {"campaigns": campaigns_list}


@app.get("/campaigns/{c_id}", status_code=200)
async def read_campaign_by_id(c_id: int):
    for each_campaign in campaigns_list:
        if each_campaign["campaign_id"] == c_id:
            return {"campaigns": each_campaign}
    raise HTTPException(status_code=404, detail="Campaign not found")


@app.post("/campaigns", status_code=201)
async def create_campaign(body: dict[str, Any]):
    new: Any = {
        "campaign_id": randint(1, 100),
        "name": body["name"],
        "due_date": body.get("due_date"),
        "created_at": datetime.now().strftime("%B %d, %Y %I:%M %p"),
    }
    campaigns_list.append(new)
    return {"campaigns": new}


@app.put("/campaigns/{c_id}", status_code=201)
async def update_campaign(body: dict[str, Any], c_id: int):
    for index, campaign in enumerate(campaigns_list):
        if campaign["campaign_id"] == c_id:
            updated: Any = {
                "campaign_id": c_id,
                "name": body["name"],
                "due_date": body.get("due_date"),
                "created_at": campaign["created_at"],
            }

            campaigns_list[index] = updated
            return {"campaigns": updated}

    raise HTTPException(status_code=404, detail="Campaign not updated")


@app.delete("/campaigns/{c_id}")
async def deleted_campaign(c_id: int):
    for index, campaign in enumerate(campaigns_list):
        if campaign["campaign_id"] == c_id:
            campaigns_list.pop(index)
            return Response(status_code=204)
    raise HTTPException(status_code=404, detail="Campaign not deleted")


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
