from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from routers.auth.oauth2 import get_current_user
from database.models import Todo, TodoCreate, TodoUpdate, User
from database.connection import SessionDep
from sqlmodel import select, func, case
from datetime import datetime, timezone

router = APIRouter(prefix="/todo", tags=["todo"])


@router.get("/all")
def get_todos(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
    category: str | None = None,
    status: str | None = None,
):

    base_query = select(Todo).where(
        Todo.user_id == current_user.id, Todo.category == category
    )

    count_query = select(func.count()).where(
        Todo.user_id == current_user.id, Todo.category == category
    )

    all_todos_count = session.exec(count_query).one()

    # Kategória szűrés (opcionális)
    if category:
        base_query = base_query.where(Todo.category == category)
        count_query = count_query.where(Todo.category == category)

    # Státusz szűrés (opcionális)
    if status:
        base_query = base_query.where(Todo.status == status)

    # Rendezés (SQL Server-kompatibilis!)
    filtered_query = base_query.order_by(
        case((Todo.status == "done", 1), else_=0),
        case((Todo.deadline.is_(None), 1), else_=0),
        Todo.deadline.asc(),
        Todo.created_at.asc(),
    )

    all_todos_count = session.exec(count_query).one()
    filtered_todos = session.exec(filtered_query).all()

    return {"all_count": all_todos_count, "filtered": filtered_todos}


@router.get("/stats")
def get_todo_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
):
    # SQL query a kategóriánkénti csoportosításhoz
    query = (
        select(Todo.category, func.count(Todo.id).label("count"))
        .where(Todo.user_id == current_user.id)
        .group_by(Todo.category)
    )

    results = session.exec(query).all()

    # Alapértelmezett értékek minden kategóriához
    stats = {"personal": 0, "work": 0, "development": 0, "total": 0}

    # Feltöltjük a tényleges értékekkel

    for category, count in results:
        if category in stats:
            stats[category] = count

    return [
        {"name": "personal", "count": stats["personal"]},
        {"name": "work", "count": stats["work"]},
        {"name": "development", "count": stats["development"]},
    ]


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_todo(
    todo: TodoCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
):
    db_todo = Todo(**todo.model_dump(), user_id=current_user.id)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo


@router.patch("/{todo_id}")
def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
):
    db_todo = session.get(Todo, todo_id)

    if not db_todo or db_todo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Todo not found")

    for field, value in todo_update.model_dump(exclude_unset=True).items():
        setattr(db_todo, field, value)

    db_todo.modified_at = datetime.now(timezone.utc)

    # db_todo.title = todo_update.title
    # db_todo.modify_at = datetime.now(timezone.utc)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo


@router.delete("/{todo_id}")
def delete_todo(
    todo_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
):
    todo = session.get(Todo, todo_id)
    if not todo or todo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Todo not found")
    session.delete(todo)
    session.commit()
    return {"ok": True}
