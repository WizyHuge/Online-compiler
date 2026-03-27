# ______________import_____________
from flask import Flask, request, jsonify, render_template, Response, url_for, redirect, g
from flask_login import login_user, login_required, logout_user, LoginManager, current_user

from forms.login_form import LoginForm
from forms.register_form import RegisterForm

from data.users import User
from data.file import File
from data.posts import Post, PostFile
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
    db_sess = get_db()
    return db_sess.get(User, user_id)

@app.route('/')
def index():
    db_sess = get_db()
    all_posts = db_sess.query(Post).order_by(Post.created_date.desc()).all()
    return render_template('index.html', posts=all_posts, title='Главная')

@app.route('/editor')
@login_required
def editor():
    return render_template('editor.html', title='Editor')

@app.route('/posts/create', methods=['GET', 'POST'])
@login_required
def create_post():
    db_sess = get_db()

    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        file_ids = data.get('file_ids', [])

        if not title or not file_ids:
            return jsonify({"error": "Укажи заголовок и хотя бы один файл"}), 400

        user_files = db_sess.query(File).filter(
            File.id.in_(file_ids),
            File.user_id == current_user.id
        ).all()

        if len(user_files) != len(file_ids):
            return jsonify({"error": "Один из файлов не найден"}), 403

        post = Post()
        post.user_id = current_user.id
        post.title = title
        post.description = description
        db_sess.add(post)
        db_sess.flush()

        for order, file_id in enumerate(file_ids):
            pf = PostFile()
            pf.post_id = post.id
            pf.file_id = file_id
            pf.order = order
            db_sess.add(pf)

        db_sess.commit()
        return jsonify({"id": post.id}), 201

    user_files = db_sess.query(File).filter(File.user_id == current_user.id).all()
    return render_template('create_post.html', files=user_files, title='Новый пост')

@app.route('/posts/<int:post_id>/files', methods=["GET"])
def get_post_files(post_id):
    db_sess = get_db()
    post = db_sess.query(Post).filter(Post.id == post_id).first()
    if not post:
        return jsonify({"error": "Пост не найден"}), 404
    return jsonify([
        {"id": pf.file.id, "name": pf.file.name, "code": pf.file.get_code()}
        for pf in post.post_files
    ])
    
@app.route('/posts/<int:post_id>', methods=["DELETE"])
@login_required
def delete_post(post_id):
    db_sess = get_db()
    post = db_sess.query(Post).filter(Post.id == post_id).first()
    if not post:
        return jsonify({"error": "Пост не найден"}), 404
    db_sess.delete(post)
    db_sess.commit()
    return jsonify({"ok": True})
    
@app.route('/api/files', methods=['GET'])
@login_required
def get_files():
    db_sess = get_db()
    user_files = db_sess.query(File).filter(File.user_id == current_user.id).all()
    return jsonify([
        {"id": f.id, "name": f.name, "created_date": str(f.created_date)}
        for f in user_files
    ])


@app.route('/api/files', methods=['POST'])
@login_required
def create_file():
    data = request.get_json()
    name = data.get('name', 'main.py').strip()
    code = data.get('code', '')

    db_sess = get_db()
    f = File()
    f.user_id = current_user.id
    f.name = name
    f.set_code(code)
    db_sess.add(f)
    db_sess.commit()
    return jsonify({"id": f.id, "name": f.name}), 201


@app.route('/api/files/<int:file_id>', methods=['GET'])
@login_required
def get_file(file_id):
    db_sess = get_db()
    f = db_sess.query(File).filter(
        File.id == file_id,
        File.user_id == current_user.id
    ).first()
    if not f:
        return jsonify({"error": "Файл не найден"}), 404
    return jsonify({"id": f.id, "name": f.name, "code": f.get_code()})


@app.route('/api/files/<int:file_id>', methods=['PUT'])
@login_required
def update_file(file_id):
    db_sess = get_db()
    f = db_sess.query(File).filter(
        File.id == file_id,
        File.user_id == current_user.id
    ).first()
    if not f:
        return jsonify({"error": "Файл не найден"}), 404

    data = request.get_json()
    if 'name' in data:
        f.name = data['name'].strip()
    if 'code' in data:
        f.set_code(data['code'])

    db_sess.commit()
    return jsonify({"ok": True})


@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    db_sess = get_db()
    f = db_sess.query(File).filter(
        File.id == file_id,
        File.user_id == current_user.id
    ).first()
    if not f:
        return jsonify({"error": "Файл не найден"}), 404
    db_sess.delete(f)
    db_sess.commit()
    return jsonify({"ok": True})

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
        db_session = get_db()
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
        db_sess = get_db()
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

def get_db():
    if 'db_sess' not in g:
        g.db_sess = db.create_session()
    return g.db_sess

@app.teardown_appcontext
def close_db(error):
    db_sess = g.pop('db_sess', None)
    if db_sess is not None:
        db_sess.close()
    

# ______________start_____________
def main():
    db.global_init("db/database.db")
    app.run(debug=True)

if __name__ == "__main__":
    main()