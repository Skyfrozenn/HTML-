from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, relationship
from sqlalchemy import func, ForeignKey,select,desc


from datetime import datetime

Base = declarative_base()
engine = create_engine("sqlite:///database.db")
Session = sessionmaker(engine)

class Users(Base):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name : Mapped[str]
    password : Mapped[str]
    joined : Mapped[datetime] = mapped_column(server_default=func.now())
    user_task : Mapped[list["Tasks"]] = relationship(back_populates="task_user",lazy = "joined")


class Tasks(Base):
    __tablename__ = "tasks"
    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id : Mapped[int] = mapped_column(ForeignKey(Users.id)) #внешний ключ
    name : Mapped[str]
    description : Mapped[str]
    status: Mapped[str] = mapped_column(default="не выполнено")
    data : Mapped[datetime] = mapped_column(server_default=func.now())

     # Дата изменения (NULL по умолчанию, меняется вручную)
    updated_at: Mapped[str] = mapped_column(default="Не изменялось", nullable=True)
    # Дата выполнения (NULL по умолчанию, меняется вручную)
    completed_at: Mapped[str] = mapped_column(default="Еще не выполнено",nullable=True)

    task_user : Mapped["Users"] = relationship(back_populates="user_task",lazy = "joined")



 
 