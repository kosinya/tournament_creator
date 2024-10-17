from sqlalchemy.orm import Session

from dto import department as dto
from models.department import Department


# Получить список всех отделений
def get_all_departments(db: Session):
    return db.query(Department).all()


# Получить отделение по id
def get_department_by_id(db: Session, department_id: int):
    return db.query(Department).filter_by(id=department_id).first()


# Создать новое отделение
def create_department(db: Session, data: dto.DepartmentCreate = None):
    new_department = Department(name=data.name)
    try:
        db.add(new_department)
        db.commit()
        db.refresh(new_department)
    except Exception as e:
        print(e)
        db.rollback()

    return new_department


# Изменить отделение по id
def update_department(db: Session, department_id: int, data: dto.Department):
    dep = db.query(Department).filter_by(id=department_id).first()
    dep.name = data.name

    try:
        db.add(dep)
        db.commit()
        db.refresh(dep)
    except Exception as e:
        print(e)
        db.rollback()

    return dep


# Удалить отделение по id
def delete_department(db: Session, department_id: int):
    dep = get_department_by_id(db, department_id)
    db.delete(dep)
    db.commit()
    return dep
