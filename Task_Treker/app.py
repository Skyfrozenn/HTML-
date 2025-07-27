from flask import Flask, render_template, request, jsonify,redirect,url_for,session

from math import ceil

from datetime import datetime

from functools import wraps
from datetime import timedelta
from database import  Session,  Users, Tasks,select,func,desc
from argon2 import PasswordHasher, exceptions

import os
 

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30) # время активности сессии после очищается

ph = PasswordHasher(time_cost=3, memory_cost=66536, parallelism=4)



def check_login(func): #Декоратор 
    @wraps(func) # для декоратов чтобы сохранило все данные
    def wraper(*args, **kwargs): # Улучшеная функция наша 
        if "user_id" not in session:
            return redirect(url_for("logout"))
        
        else:
            return func(*args, **kwargs)
    
    return wraper



@app.get("/") # Регистрация
def start_page():
    return render_template("index.html")

@app.post("/registration") #Успешная регистрация и вход в профиль
def reg():
    name_user = request.form.get("name")
    password = request.form.get("password")

    if not name_user or not password:
        return "Вы ввели не все данные!",400

    with Session.begin() as db_session: 
        existing_user = db_session.scalar(select(Users).where(Users.name == name_user))
        if existing_user:
            try:
                ph.verify(existing_user.password, password)
                return "Юзер уже существует!",400
            except exceptions.VerifyMismatchError: 
                return "Некоректные данные! Для существующего юзера",400
             
        else:
            hashed_password = ph.hash(password) # зашифровали перед добавлением в бд
            new_user = Users(name=name_user, password = hashed_password) # и тут зашифруй
            db_session.add(new_user)
            db_session.flush() #сохранили в черновик
            

            session["user_id"] = new_user.id #ЛОБАВИЛИ в сессию фласка
            session["username"] = new_user.name

    return redirect(url_for("profile"))

@app.get("/profile") #ПРОФИЛЬ
@check_login
def profile():
    id = session["user_id"]
    with Session() as db_session:
        user_page = db_session.scalar(select(Users).where(Users.id == id))
        return render_template("profile.html",user=user_page.name, data = user_page.joined)

     


@app.get("/entrance")
def logout():
    return render_template("login.html")


@app.post("/login") #вход в профиль
def authoresation():
    name = request.form.get("name")
    password = request.form.get("password")
    with Session() as db_session:
        user = db_session.scalar(select(Users).where(Users.name == name))
        if user and ph.verify(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.name
            return redirect(url_for("profile"))
        else:
            return "Неверные данные!",400
        
@app.post("/exit")
def end():
    session.clear()
    return redirect(url_for("start_page"))

@app.post("/add_task")
@check_login
def add_task():
    name_task = request.form.get("name_task") 
    description_task = request.form.get("description-task")
    user_id = session["user_id"]
    with Session.begin() as db_session:
        new_task = Tasks(user_id = user_id, name = name_task, description = description_task)
        db_session.add(new_task)
        return redirect(url_for("watch_tovars", page = 1))

@app.get("/view_products/<int:page>")
@check_login
def watch_tovars(page):
    user_id = session["user_id"]
    per_page = 3
    
    with Session() as db_session:
        # Получаем задачи для текущей страницы
        user_product = db_session.scalars(
            select(Tasks)
            .where(Tasks.user_id == user_id)
            .where(Tasks.status == "не выполнено")
            .order_by(desc(Tasks.data))
            .offset((page-1) * per_page)
            .limit(per_page)
        ).unique().all()

        # Общее количество НЕВЫПОЛНЕННЫХ задач
        count = db_session.scalar(
            select(func.count(Tasks.id))
            .where(Tasks.user_id == user_id)
            .where(Tasks.status == "не выполнено")  # ← Важно!
        )
        
        user_name = session["username"]  # Упростил получение имени
        
        # Правильный расчёт максимальной страницы
        max_page = max(1, ceil(count / per_page))  
        
        # Корректируем запрошенную страницу, если она превышает максимум
        page = min(page, max_page)

    return render_template(
        "view_products.html",
        user_name=user_name,
        page=page,
        tasks=user_product,
        total_page=max_page  # ← Теперь передаём корректное значение!
    )

@app.get("/update_task/<int:page>/<int:id>")
@check_login
def update_task(page,id): #передали страницу ,чтобы после изменения на ту же защел и передали айди для дальнейшнего изменения
    with Session() as db_session:
        task = db_session.scalar(select(Tasks).where(Tasks.id == id))

    if task:
        return render_template("view_task.html",task = task,page=page)
    else:
        return "Задача не найдена!",404
     
     
@app.post("/save_new_task")
@check_login
def save_new_task():
    if request.form.get("_method") == "put":
        page = request.form.get("page")
        id_task = request.form.get("task_id")
        new_name = request.form.get("new_name_task")
        new_description = request.form.get("new_description_task")

        with Session.begin() as db_session:
            task = db_session.scalar(select(Tasks).where(Tasks.id == id_task))
            task.name = new_name
            task.description = new_description
            now = datetime.now()
            task.updated_at = now.strftime("%Y-%m-%d %H:%M:%S")
        return redirect(url_for('watch_tovars', page = page))
    
    else:
        return "Неверный метод!",405


 

@app.post("/delete_task")
@check_login
def delete_task():
    if request.form.get("_method") == "delete":
        page = int(request.form.get("page", 1))  # Текущая страница (начинается с 1)
        id_task = request.form.get("task_id")
        user_id = session["user_id"]
        
        
        with Session.begin() as db_session:
            # 1. Удаляем задачу
            task = db_session.scalar(select(Tasks).where(Tasks.id == id_task))
            if task:
                db_session.delete(task)
                db_session.flush()   
            
             
            total_tasks = db_session.scalar(
                select(func.count()).where(Tasks.user_id == user_id))
            
             
            max_page = max(1, ceil(total_tasks / 3))  # Округляем вверх
            
             
            new_page = min(page, max_page)
            
             
            
        return redirect(url_for('watch_tovars', page=new_page))
    
@app.post("/completing_the_task")
@check_login
def complete_task():
    task_id = request.form.get("task_id")
    current_page = request.form.get("current_page", 1, type=int)
    
    with Session.begin() as db_session:
        # Помечаем задачу выполненной
        task = db_session.scalar(select(Tasks).where(Tasks.id == task_id))
        task.status = "Выполнено"
        task.completed_at = datetime.now()
    
    # Всегда перенаправляем на первую страницу выполненных задач
    return redirect(url_for('watch_completed_task', page=1, prev_page=current_page, source='task'))



        
@app.get("/watch_task_completed/<int:page>")
@check_login
def watch_completed_task(page): 
    PER_PAGE = 3
    prev_page = request.args.get("prev_page", type=int)  # Добавляем default
    source = request.args.get("source")  # Добавляем default
    
    user_id = session["user_id"]
    username = session["username"]
    
    with Session() as db_session:
        count = db_session.scalar(
            select(func.count(Tasks.id))
            .where(Tasks.user_id == user_id)
            .where(Tasks.status == "Выполнено")
        )
        total_page = max(1, ceil(count / PER_PAGE))
        current_page = min(max(1, page), total_page)
        
        completed_tasks = db_session.scalars(
            select(Tasks)
            .where(Tasks.user_id == user_id)
            .where(Tasks.status == "Выполнено")
            .order_by(desc(Tasks.completed_at))
            .offset((current_page - 1) * PER_PAGE)
            .limit(PER_PAGE)
        ).unique().all()

    return render_template(
        "completed_task.html",
        username=username,
        tasks=completed_tasks,
        page=current_page,
        count=total_page,
        prev_page=prev_page,
        source=source
    )
    
@app.get("/update_profiles")
@check_login
def update_profile():
    user_name = session["username"]  
    return render_template("update_profile.html",username = user_name)
 

@app.post("/save_update_user")
@check_login
def save_update_user():
    # Жестко берем данные из формы
    new_name = request.form.get("new_name")  
    current_password = request.form.get("password")
    new_password = request.form.get("new_password")
    
    user_id = session["user_id"]
    
    with Session.begin() as db_session:
        # Берем юзера из базы
        user = db_session.scalar(select(Users).where(Users.id == user_id))
        
        # Проверяем пароль в лоб
        try:
            ph.verify(user.password, current_password)
        except exceptions.VerifyMismatchError:
            return "Неверный пароль, брат!", 400
        
        # Меняем имя если есть
        if new_name:
            user.name = new_name
            session["username"] = new_name
        
        # Меняем пароль если есть
        if new_password:
            user.password = ph.hash(new_password)
    
    return redirect(url_for("profile"))




if __name__ == "__main__":
     
    app.run(debug=True)
    
#РАБОТАЕТ ehff