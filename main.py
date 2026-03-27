# ______________import_____________
from flask import Flask, request, jsonify, render_template, Response, url_for, redirect
from flask_login import login_user, login_required, logout_user, LoginManager

from forms.login_form import LoginForm
from forms.register_form import RegisterForm

from data.users import User
from data import db

import redis
import json
import uuid
import time


#_______________init_______________

app = Flask(__name__)
app.config["SECRET_KEY"] = 'f959fc589c1b0c1e5fcb03c8d480d14499902624862252d3b30de1dd40f9bc45'
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

login_manager = LoginManager()
login_manager.init_app(app)

# ______________routes____________

@login_manager.user_loader
def load_user(user_id):
    db_sess = db.create_session()
    return db_sess.get(User, user_id)

@app.route('/')
def index():
    return render_template('index.html', title='Main Page')

@app.route('/editor')
@login_required
def editor():
    return render_template('editor.html', title='Editor')

@app.route("/api/run", methods=["POST"])
def run_code():
    data = request.get_json()
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"error": "Код пустой"}), 400

    ip = request.remote_addr
    rate_key = f"rate:{ip}"
    count = r.incr(rate_key)
    if count == 1:
        r.expire(rate_key, 60)
    if count > 5:
        return jsonify({"error": "Слишком много запросов, подожди минуту"}), 429

    task_id = str(uuid.uuid4())
    task = {"id": task_id, "code": code}
    r.lpush("tasks", json.dumps(task))

    return jsonify({"task_id": task_id})

@app.route("/api/stream/<task_id>")
def stream(task_id):
    def generate():
        for _ in range(150):
            result = r.get(f"result:{task_id}")
            if result:
                yield f"data: {result}\n\n"
                return
            time.sleep(0.1)
        yield f"data: {json.dumps({'error': 'Таймаут выполнения'})}\n\n"

    return Response(generate(), mimetype="text/event-stream")

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_session = db.create_session()
        user = db_session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template("login.html",
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template("login.html", title="Авторизация", form=form)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)
    

# ______________start_____________
def main():
    db.global_init("db/database.db")
    app.run(debug=True)

if __name__ == "__main__":
    main()