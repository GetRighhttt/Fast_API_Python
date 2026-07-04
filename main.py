from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Generic, Optional, TypeVar

from fastapi import Depends, FastAPI, HTTPException, Response, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Field, Session, SQLModel, create_engine, select
from starlette.requests import Request
from typing_extensions import Annotated

T = TypeVar("T")


# response models
class ApiResponse(BaseModel, Generic[T]):
    data: T
    message: Optional[str] = None
    meta: Optional[dict] = None


class PaginatedResponse(BaseModel, Generic[T]):
    data: T
    next: Optional[str] = None
    prev: Optional[str] = None
    message: Optional[str] = None
    meta: Optional[dict] = None


# database models
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


# mapper models for documentation
class CampaignCreate(BaseModel):
    name: str
    due_date: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    name: str
    due_date: Optional[datetime] = None


class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str


class EmployeeUpdate(BaseModel):
    first_name: str
    last_name: str


# creating database engine
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# session is kind of like the repository for the db - source of truth
def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()

    with Session(engine) as session:
        if session.exec(select(Campaign)).first() is None:
            session.add_all([
                Campaign(name="Q3 Customer Retention Initiative", due_date=datetime.now(timezone.utc)),
                Campaign(name="Summer Product Launch", due_date=datetime.now(timezone.utc)),
                Campaign(name="Back-to-School Promotion", due_date=datetime.now(timezone.utc)),
                Campaign(name="Holiday Email Marketing", due_date=datetime.now(timezone.utc)),
                Campaign(name="Enterprise Lead Generation", due_date=datetime.now(timezone.utc)),
                Campaign(name="Spring Customer Acquisition", due_date=datetime.now(timezone.utc)),
                Campaign(name="Referral Rewards Program", due_date=datetime.now(timezone.utc)),
                Campaign(name="Black Friday Sales Event", due_date=datetime.now(timezone.utc)),
                Campaign(name="Customer Feedback Survey", due_date=datetime.now(timezone.utc)),
                Campaign(name="New Feature Awareness Campaign", due_date=datetime.now(timezone.utc)),
                Campaign(name="Premium Subscription Upgrade", due_date=datetime.now(timezone.utc)),
                Campaign(name="Mobile App Engagement Drive", due_date=datetime.now(timezone.utc)),
                Campaign(name="Loyalty Program Enrollment", due_date=datetime.now(timezone.utc)),
                Campaign(name="Year-End Customer Appreciation", due_date=datetime.now(timezone.utc)),
                Campaign(name="Product Webinar Registration", due_date=datetime.now(timezone.utc)),
            ])

        if session.exec(select(Employee)).first() is None:
            session.add_all([
                Employee(first_name="Emma", last_name="Johnson"),
                Employee(first_name="Michael", last_name="Chen"),
                Employee(first_name="Olivia", last_name="Martinez"),
                Employee(first_name="David", last_name="Wilson"),
                Employee(first_name="Sophia", last_name="Patel"),
                Employee(first_name="James", last_name="Anderson"),
                Employee(first_name="Charlotte", last_name="Brown"),
                Employee(first_name="Benjamin", last_name="Davis"),
                Employee(first_name="Amelia", last_name="Garcia"),
                Employee(first_name="William", last_name="Harris"),
                Employee(first_name="Mia", last_name="Lewis"),
                Employee(first_name="Lucas", last_name="Walker"),
                Employee(first_name="Evelyn", last_name="Hall"),
                Employee(first_name="Henry", last_name="Allen"),
                Employee(first_name="Ava", last_name="Young"),
            ])

        session.commit()

    yield


app = FastAPI(root_path="/api/v1", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Root endpoint of the API"}


@app.get("/campaigns/page", response_model=ApiResponse[list[Campaign]], status_code=200)
async def read_campaigns_by_page_with_offset(
        session: SessionDep,
        page: int = Query(1, ge=1)
):
    # set hard limits and offsets
    limit = 3
    offset = (page - 1) * limit
    campaigns = session.exec(select(Campaign).order_by(Campaign.campaign_id).offset(offset).limit(limit)).all()

    return ApiResponse(
        data=campaigns,
        message="Campaigns retrieved successfully",
        meta={"count": len(campaigns)},
    )


@app.get("/campaigns/page_size", response_model=PaginatedResponse[list[Campaign]], status_code=200)
async def read_campaigns_by_page_and_page_size_with_offset(
        request: Request,
        session: SessionDep,
        page: int = Query(1, ge=1),
        page_size: int = Query(3, ge=1),
):
    # establish offset and get total count
    offset = (page - 1) * page_size

    campaigns = session.exec(
        select(Campaign)
        .order_by(Campaign.campaign_id)
        .offset(offset)
        .limit(page_size)
    ).all()

    total = session.exec(
        select(func.count()).select_from(Campaign)
    ).one()

    # prep next and prev url to consume
    base_url = str(request.url).split("?")[0]

    next_url = (
        f"{base_url}?page={page + 1}&page_size={page_size}"
        if offset + page_size < total
        else None
    )

    prev_url = (
        f"{base_url}?page={page - 1}&page_size={page_size}"
        if page > 1
        else None
    )

    return PaginatedResponse(
        data=campaigns,
        next=next_url,
        prev=prev_url,
        message="Campaigns retrieved successfully",
        meta={
            "count": len(campaigns),
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    )


@app.get("/campaigns/limit", response_model=PaginatedResponse[list[Campaign]], status_code=200)
async def read_campaigns_by_limit_with_offset(
        request: Request,
        session: SessionDep,
        offset: int = Query(0, ge=0),
        limit: int = Query(3, ge=1),
):
    campaigns = session.exec(
        select(Campaign)
        .order_by(Campaign.campaign_id)
        .offset(offset)
        .limit(limit)
    ).all()

    # prep next and prev url to consume
    base_url = str(request.url).split("?")[0]
    next_url = f"{base_url}?offset={offset + limit}&limit={limit}"
    prev_url = (
        f"{base_url}?offset={max(0, offset - limit)}&limit={limit}"
        if offset > 0
        else None
    )

    return PaginatedResponse(
        data=campaigns,
        next=next_url,
        prev=prev_url,
        message="Campaigns retrieved successfully",
        meta={"count": len(campaigns), },
    )


@app.get("/campaigns/{campaign_id}", response_model=ApiResponse[Campaign], status_code=200)
async def read_campaign_by_id(
        campaign_id: int,
        session: SessionDep
):
    campaign = session.get(Campaign, campaign_id)

    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return ApiResponse(
        data=campaign,
        message="Campaign retrieved successfully",
    )


@app.post("/campaigns", response_model=ApiResponse[Campaign], status_code=201)
async def create_campaign(
        body: CampaignCreate,
        session: SessionDep
):
    campaign = Campaign(
        name=body.name,
        due_date=body.due_date,
    )

    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    return ApiResponse(
        data=campaign,
        message="Campaign created successfully",
    )


@app.put("/campaigns/{campaign_id}", response_model=ApiResponse[Campaign], status_code=200)
async def update_campaign(
        campaign_id: int,
        body: CampaignUpdate,
        session: SessionDep,
):
    campaign = session.get(Campaign, campaign_id)

    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.name = body.name
    campaign.due_date = body.due_date

    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    return ApiResponse(
        data=campaign,
        message="Campaign updated successfully",
    )


@app.delete("/campaigns/{campaign_id}", status_code=204)
async def delete_campaign(
        campaign_id: int,
        session: SessionDep
):
    campaign = session.get(Campaign, campaign_id)

    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    session.delete(campaign)
    session.commit()

    return Response(status_code=204)


@app.get("/employees", response_model=ApiResponse[list[Employee]], status_code=200)
async def read_employees(session: SessionDep):
    employees = session.exec(select(Employee)).all()

    return ApiResponse(
        data=employees,
        message="Employees retrieved successfully",
        meta={"count": len(employees)},
    )


@app.get("/employees/{employee_id}", response_model=ApiResponse[Employee], status_code=200)
async def read_employee_by_id(
        employee_id: int,
        session: SessionDep
):
    employee = session.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    return ApiResponse(
        data=employee,
        message="Employee retrieved successfully",
    )


@app.get("/employees/search/{employee_name}", response_model=ApiResponse[Employee], status_code=200)
async def read_first_or_last_employee_name(
        employee_name: str,
        session: SessionDep
):
    statement = select(Employee).where(
        (Employee.first_name == employee_name) | (Employee.last_name == employee_name)
    )

    employee = session.exec(statement).first()

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    return ApiResponse(
        data=employee,
        message="Employee retrieved successfully",
    )


@app.post("/employees", response_model=ApiResponse[Employee], status_code=201)
async def create_employee(
        body: EmployeeCreate,
        session: SessionDep
):
    employee = Employee(
        first_name=body.first_name,
        last_name=body.last_name,
    )

    session.add(employee)
    session.commit()
    session.refresh(employee)

    return ApiResponse(
        data=employee,
        message="Employee created successfully",
    )


@app.put("/employees/{employee_id}", response_model=ApiResponse[Employee], status_code=200)
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

    return ApiResponse(
        data=employee,
        message="Employee updated successfully",
    )


@app.delete("/employees/{employee_id}", status_code=204)
async def delete_employee(
        employee_id: int,
        session: SessionDep
):
    employee = session.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    session.delete(employee)
    session.commit()

    return Response(status_code=204)
