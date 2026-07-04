from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Response
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing_extensions import Annotated


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


class CampaignCreate(BaseModel):
    name: str
    due_date: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    name: str
    due_date: Optional[datetime] = None


class CampaignResponse(BaseModel):
    campaign: Campaign


class CampaignsResponse(BaseModel):
    campaigns: List[Campaign]


class PersonCreate(BaseModel):
    first_name: str
    last_name: str


class PersonUpdate(BaseModel):
    first_name: str
    last_name: str


class PersonResponse(BaseModel):
    person: Person


class PersonsResponse(BaseModel):
    names: List[Person]


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
    # create database
    create_db_and_tables()

    # if nothing present, fill both tables with starter data
    with Session(engine) as session:
        if session.exec(select(Campaign)).first() is None:
            session.add_all([
                Campaign(name="NBA Campaign", due_date=datetime.now(timezone.utc)),
                Campaign(name="NFL Campaign", due_date=datetime.now(timezone.utc)),
                Campaign(name="FIFA Campaign", due_date=datetime.now(timezone.utc)),
                Campaign(name="NHL Campaign", due_date=datetime.now(timezone.utc)),
                Campaign(name="TRACK Campaign", due_date=datetime.now(timezone.utc)),
            ])

        if session.exec(select(Person)).first() is None:
            session.add_all([
                Person(first_name="Stefan", last_name="Bayne"),
                Person(first_name="Vincent", last_name="Terome"),
                Person(first_name="Shawn", last_name="Terez"),
                Person(first_name="ManInThe", last_name="Middle"),
            ])

        session.commit()
    # yields for setup then will continue after yield
    yield


app = FastAPI(root_path="/api/v1", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Root endpoint of the API"}


@app.get("/campaigns", response_model=CampaignsResponse, status_code=200)
async def read_campaigns(session: SessionDep):
    campaigns = session.exec(select(Campaign)).all()
    return {"campaigns": campaigns}


@app.get("/campaigns/{c_id}", response_model=CampaignResponse, status_code=200)
async def read_campaign_by_id(c_id: int, session: SessionDep):
    campaign = session.get(Campaign, c_id)

    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return {"campaign": campaign}


@app.post("/campaigns", response_model=CampaignResponse, status_code=201)
async def create_campaign(body: CampaignCreate, session: SessionDep):
    campaign = Campaign(
        name=body.name,
        due_date=body.due_date,
    )

    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    return {"campaign": campaign}


@app.put("/campaigns/{c_id}", response_model=CampaignResponse, status_code=200)
async def update_campaign(c_id: int, body: CampaignUpdate, session: SessionDep):
    campaign = session.get(Campaign, c_id)

    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.name = body.name
    campaign.due_date = body.due_date

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


@app.get("/names", response_model=PersonsResponse, status_code=200)
async def read_names(session: SessionDep):
    people = session.exec(select(Person)).all()
    return {"names": people}


@app.get("/names/id/{p_id}", response_model=PersonResponse, status_code=200)
async def read_person_by_id(p_id: int, session: SessionDep):
    person = session.get(Person, p_id)

    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    return {"person": person}


@app.get("/names/search/{person_name}", response_model=PersonResponse, status_code=200)
async def read_first_or_last_name(person_name: str, session: SessionDep):
    statement = select(Person).where(
        (Person.first_name == person_name) | (Person.last_name == person_name)
    )

    person = session.exec(statement).first()

    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    return {"person": person}


@app.post("/names", response_model=PersonResponse, status_code=201)
async def create_person(body: PersonCreate, session: SessionDep):
    person = Person(
        first_name=body.first_name,
        last_name=body.last_name,
    )

    session.add(person)
    session.commit()
    session.refresh(person)

    return {"person": person}


@app.put("/names/{p_id}", response_model=PersonResponse, status_code=200)
async def update_person(p_id: int, body: PersonUpdate, session: SessionDep):
    person = session.get(Person, p_id)

    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    person.first_name = body.first_name
    person.last_name = body.last_name

    session.add(person)
    session.commit()
    session.refresh(person)

    return {"person": person}


@app.delete("/names/{p_id}", status_code=204)
async def delete_person(p_id: int, session: SessionDep):
    person = session.get(Person, p_id)

    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    session.delete(person)
    session.commit()

    return Response(status_code=204)
