from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import create_access_token, get_current_user
from app.database import Base, engine, get_db
from app.security import hash_password, verify_password

app = FastAPI(title="Expense Tracker API")

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Expense Tracker API is running!"}


@app.post("/register", response_model=schemas.UserResponse)
def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    existing = (
        db.query(models.User)
        .filter(
            (models.User.email == user.email)
            | (models.User.username == user.username)
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )

    new_user = models.User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    db_user = (
    db.query(models.User)
    .filter(models.User.email == form_data.username)
    .first()
)

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={"sub": db_user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
@app.get("/me", response_model=schemas.UserResponse)
def get_me(
    current_user: models.User = Depends(get_current_user)
):
    return current_user

@app.post("/expenses", response_model=schemas.ExpenseResponse)
def create_expense(
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_expense = models.Expense(
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        owner_id=current_user.id
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    return new_expense
@app.put("/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
def update_expense(
    expense_id: int,
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_expense = (
        db.query(models.Expense)
        .filter(
            models.Expense.id == expense_id,
            models.Expense.owner_id == current_user.id
        )
        .first()
    )

    if not db_expense:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    db_expense.title = expense.title
    db_expense.amount = expense.amount
    db_expense.category = expense.category

    db.commit()
    db.refresh(db_expense)

    return db_expense

@app.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    expense = (
        db.query(models.Expense)
        .filter(
            models.Expense.id == expense_id,
            models.Expense.owner_id == current_user.id
        )
        .first()
    )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    db.delete(expense)
    db.commit()

    return {
        "message": "Expense deleted successfully"
    }
    

@app.get("/expenses", response_model=list[schemas.ExpenseResponse])
def get_expenses(
    category: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 10,
    sort_by: str | None = None,
    order: str = "asc",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = (
        db.query(models.Expense)
        .filter(models.Expense.owner_id == current_user.id)
    )
    if category:
        query = query.filter(models.Expense.category == category)

    if search:
        query = query.filter(
            models.Expense.title.ilike(f"%{search}%")
        )
    if sort_by == "amount":
        if order == "desc":
            query = query.order_by(models.Expense.amount.desc())
        else:
             query = query.order_by(models.Expense.amount.asc())

    elif sort_by == "created_at":
        if order == "desc":
            query = query.order_by(models.Expense.created_at.desc())
        else:
            query = query.order_by(models.Expense.created_at.asc())

    elif sort_by == "title":
        if order == "desc":
            query = query.order_by(models.Expense.title.desc())
        else:
            query = query.order_by(models.Expense.title.asc())
    expenses = (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )

    return expenses

@app.get("/summary")
def expense_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    total_expenses = (
        db.query(models.Expense)
        .filter(models.Expense.owner_id == current_user.id)
        .count()
    )

    total_amount = (
        db.query(func.sum(models.Expense.amount))
        .filter(models.Expense.owner_id == current_user.id)
        .scalar()
    )

    average = (
        total_amount / total_expenses
        if total_expenses > 0
        else 0
    )

    return {
        "total_expenses": total_expenses,
        "total_amount": total_amount or 0,
        "average_expense": round(average, 2)
    }

@app.get(
    "/summary/categories",
    response_model=dict[str, float]
)
def category_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    results = (
        db.query(
            models.Expense.category,
            func.sum(models.Expense.amount)
        )
        .filter(models.Expense.owner_id == current_user.id)
        .group_by(models.Expense.category)
        .all()
    )

    return {
        category: total
        for category, total in results
    }
