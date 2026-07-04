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


class Employee(SQLModel, table=True):
    employee_id: Optional[int] = Field(default=None, primary_key=True)
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


class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str


class EmployeeUpdate(BaseModel):
    first_name: str
    last_name: str


class EmployeeResponse(BaseModel):
    employee: Employee


class EmployeesResponse(BaseModel):
    employees: List[Employee]


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# we will use this session for the data from the database
def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create database on app start
    create_db_and_tables()

    with Session(engine) as session:
        # if first element is empty, fill  with starter data
        if session.exec(select(Campaign)).first() is None:
            session.add_all([
                Campaign(
                    name="Q3 Customer Retention Initiative",
                    due_date=datetime.now(timezone.utc),
                ),
                Campaign(
                    name="Summer Product Launch",
                    due_date=datetime.now(timezone.utc),
                ),
                Campaign(
                    name="Back-to-School Promotion",
                    due_date=datetime.now(timezone.utc),
                ),
                Campaign(
                    name="Holiday Email Marketing",
                    due_date=datetime.now(timezone.utc),
                ),
                Campaign(
                    name="Enterprise Lead Generation",
                    due_date=datetime.now(timezone.utc),
                ),
            ])

        if session.exec(select(Employee)).first() is None:
            session.add_all([
                Employee(first_name="Emma", last_name="Johnson"),
                Employee(first_name="Michael", last_name="Chen"),
                Employee(first_name="Olivia", last_name="Martinez"),
                Employee(first_name="David", last_name="Wilson"),
                Employee(first_name="Sophia", last_name="Patel"),
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


@app.get("/employees", response_model=EmployeesResponse, status_code=200)
async def read_employees(session: SessionDep):
    employees = session.exec(select(Employee)).all()
    return {"employees": employees}


@app.get("/employees/id/{employee_id}", response_model=EmployeeResponse, status_code=200)
async def read_employee_by_id(employee_id: int, session: SessionDep):
    employee = session.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    return {"employee": employee}


@app.get("/employees/search/{employee_name}", response_model=EmployeeResponse, status_code=200)
async def read_first_or_last_employee_name(employee_name: str, session: SessionDep):
    statement = select(Employee).where(
        (Employee.first_name == employee_name) | (Employee.last_name == employee_name)
    )

    employee = session.exec(statement).first()

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    return {"employee": employee}


@app.post("/employees", response_model=EmployeeResponse, status_code=201)
async def create_employee(body: EmployeeCreate, session: SessionDep):
    employee = Employee(
        first_name=body.first_name,
        last_name=body.last_name,
    )

    session.add(employee)
    session.commit()
    session.refresh(employee)

    return {"employee": employee}


@app.put("/employees/{employee_id}", response_model=EmployeeResponse, status_code=200)
async def update_employee(
        employee_id: int,
        body: EmployeeUpdate,
        session: SessionDep,
):
    employee = session.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.first_name = body.first_name
    employee.last_name = body.last_name

    session.add(employee)
    session.commit()
    session.refresh(employee)

    return {"employee": employee}


@app.delete("/employees/{employee_id}", status_code=204)
async def delete_employee(employee_id: int, session: SessionDep):
    employee = session.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    session.delete(employee)
    session.commit()

    return Response(status_code=204)
