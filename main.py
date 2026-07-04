from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional, Annotated

from fastapi import FastAPI, HTTPException, Depends, Response
from sqlmodel import SQLModel, Field, Session, create_engine, select


class Campaign(SQLModel, table=True):
    campaign_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    due_date: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )


class Person(SQLModel, table=True):
    person_id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str = Field(index=True)
    last_name: str = Field(index=True)


# ORM - Object Relational Mapper
# take database records and convert them to objects in our code
# we are going to use SQLModel
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()

    with Session(engine) as session:
        # Campaign Table
        if not session.exec(select(Campaign, Person)).first():
            session.add_all([
                Campaign(name="NBA Campaign", due_date=datetime.now(timezone.utc)),
                Campaign(name="NFL Campaign", due_date=datetime.now(timezone.utc)),
                Campaign(name="FIFA Campaign", due_date=datetime.now(timezone.utc)),
                Campaign(name="NHL Campaign", due_date=datetime.now(timezone.utc)),
                Campaign(name="TRACK Campaign", due_date=datetime.now(timezone.utc)),
            ])

        # Person table
        if session.exec(select(Person)).first() is None:
            session.add_all([
                Person(first_name="Stefan", last_name="Bayne"),
                Person(first_name="Vincent", last_name="Terome"),
                Person(first_name="Shawn", last_name="Terez"),
                Person(first_name="ManInThe", last_name="Middle"),
            ])
        session.commit()
    yield


# how we define the app
app = FastAPI(root_path="/api/v1", lifespan=lifespan)


# declaration of the root endpoint
@app.get("/")
async def root():
    return {"message": "Root endpoint of the API"}


@app.get("/campaigns", status_code=200)
async def read_campaigns(session: SessionDep):
    campaigns = session.exec(select(Campaign)).all()
    return {"campaigns": campaigns}


@app.get("/campaigns/{c_id}", status_code=200)
async def read_campaign_by_id(c_id: int, session: SessionDep):
    campaign = session.get(Campaign, c_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"campaign": campaign}


@app.post("/campaigns", status_code=201)
async def create_campaign(body: dict[str, Any], session: SessionDep):
    campaign = Campaign(
        name=body["name"],
        due_date=body.get("due_date"),
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return {"campaign": campaign}


@app.put("/campaigns/{c_id}", status_code=200)
async def update_campaign(body: dict[str, Any], c_id: int, session: SessionDep):
    campaign = session.get(Campaign, c_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.name = body["name"]
    campaign.due_date = body.get("due_date")
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return {"campaign": campaign}


@app.delete("/campaigns/{c_id}", status_code=204)
async def delete_campaign(c_id: int, session: SessionDep):
    campaign = session.get(Campaign, c_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    session.delete(campaign)
    session.commit()
    return Response(status_code=204)


@app.get("/names")
async def read_names(session: SessionDep):
    people = session.exec(select(Person)).all()
    return {"names": people}


@app.get("/names/{person_name}")
async def read_first_or_last_name(person_name: str, session: SessionDep):
    statement = select(Person).where(
        (Person.first_name == person_name) | (Person.last_name == person_name)
    )

    person = session.exec(statement).first()
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return {"person": person}

# Manual Version of the db

# campaigns_list: Any = [
#     {
#         "campaign_id": 1,
#         "name": "Emerald Coast",
#         "due_date": lambda: datetime.now(timezone.utc),
#         "created_at": lambda: datetime.now(timezone.utc),
#     },
#     {
#         "campaign_id": 2,
#         "name": "Be the Magic",
#         "due_date": lambda: datetime.now(timezone.utc),
#         "created_at": lambda: datetime.now(timezone.utc),
#     },
#     {
#         "campaign_id": 3,
#         "name": "Wizard of Emerald",
#         "due_date": lambda: datetime.now(timezone.utc),
#         "created_at": lambda: datetime.now(timezone.utc),
#     },
#     {
#         "campaign_id": 4,
#         "name": "Oz of City",
#         "due_date": lambda: datetime.now(timezone.utc),
#         "created_at": lambda: datetime.now(timezone.utc),
#     },
# ]

# @app.get("/campaigns", status_code=200)
# async def read_campaigns(session: SessionDep):
#     campaigns = session.exec(select(Campaign)).all()
#     return {"campaigns": campaigns}
#
#
# @app.get("/campaigns/{c_id}", status_code=200)
# async def read_campaign_by_id(c_id: int):
#     for each_campaign in campaigns_list:
#         if each_campaign["campaign_id"] == c_id:
#             return {"campaigns": each_campaign}
#     raise HTTPException(status_code=404, detail="Campaign not found")
#
#
# @app.post("/campaigns", status_code=201)
# async def create_campaign(body: dict[str, Any]):
#     new: Any = {
#         "campaign_id": randint(1, 100),
#         "name": body["name"],
#         "due_date": body.get("due_date"),
#         "created_at": datetime.now(timezone.utc),
#     }
#     campaigns_list.append(new)
#     return {"campaigns": new}
#
#
# @app.put("/campaigns/{c_id}", status_code=201)
# async def update_campaign(body: dict[str, Any], c_id: int):
#     for index, campaign in enumerate(campaigns_list):
#         if campaign["campaign_id"] == c_id:
#             updated: Any = {
#                 "campaign_id": c_id,
#                 "name": body["name"],
#                 "due_date": body.get("due_date"),
#                 "created_at": campaign["created_at"],
#             }
#
#             campaigns_list[index] = updated
#             return {"campaigns": updated}
#
#     raise HTTPException(status_code=404, detail="Campaign not updated")
#
#
# @app.delete("/campaigns/{c_id}")
# async def delete_campaign(c_id: int):
#     for index, campaign in enumerate(campaigns_list):
#         if campaign["campaign_id"] == c_id:
#             campaigns_list.pop(index)
#             return Response(status_code=204)
#     raise HTTPException(status_code=404, detail="Campaign not deleted")

# person: Any = [
#     {
#         "first_name": "stefan",
#         "last_name": "lamario",
#     },
#     {
#         "first_name": "vincentjr",
#         "last_name": "terome",
#     },
#     {
#         "first_name": "shawn",
#         "last_name": "terez",
#     },
#     {
#         "first_name": "vincentsr",
#         "last_name": "teromes",
#     }
# ]
#
# @app.get("/names")
# async def read_names():
#     return {"names": person}
#
#
# @app.get("/names/{person_name}")
# async def read_first_or_last_name(person_name: str):
#     for each_name in person:
#         if each_name["first_name"] == person_name:
#             return {"first_name": each_name}
#         elif each_name["last_name"] == person_name:
#             return {"last_name": each_name}
#     raise HTTPException(status_code=404, detail="Last name not found")
