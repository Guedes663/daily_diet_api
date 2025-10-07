from flask import Flask, request, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from database import db
from models.user import User
from models.meal import Meal
from datetime import datetime
import bcrypt

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

login_manager = LoginManager()
db.init_app(app)
login_manager.init_app(app)

login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/user", methods=["POST"])
def register_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username and password:
        hashed_password = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())
        user = User(username=username, password=hashed_password, role="user")
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Usuário cadastrado com sucesso"}), 201

    return jsonify({"message": "Dados obrigatórios faltando"}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username and password:
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(str.encode(password), user.password):
            login_user(user)
            return jsonify({"message": "Usuário autenticado com sucesso"})

    return jsonify({"message": "Credenciais inválidas"}), 400

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout realizado com sucesso"})

@app.route("/meal", methods=["POST"])
@login_required
def register_meal():
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    date = data.get("date")
    time = data.get("time")
    diet = data.get("diet")

    if not (name and description and date and time and diet != None):
        return jsonify({"message": "Dados obrigatórios faltando"}), 400

    try:
        meal_datetime = datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return jsonify({"message": "Formato de data e hora deve ser YYYY-MM-DD HH:MM:SS"}), 400
        
    meal = Meal(
        name        = name, 
        description = description, 
        datetime    = meal_datetime, 
        diet        = diet, 
        id_user     = current_user.id
    )

    db.session.add(meal)
    db.session.commit()

    return jsonify({"message": "Refeição cadastrada com sucesso"}), 201
    
@app.route("/meal/<int:id_meal>", methods=["PUT"])
@login_required
def update_meal(id_meal):
    meal = Meal.query.get(id_meal)
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    date = data.get("date")
    time = data.get("time")
    diet = data.get("diet")

    if not meal:
        return jsonify({"message": "Registro não encontrado"}), 404

    if meal.id_user != current_user.id and current_user.role == "user":
        return jsonify({"message": "Você não tem permissão para alterar esse registro"}), 403
    
    if not (name or description or date or time or diet != None):
        return jsonify({"message": "Nenhum dado fornecido para atualização"}), 400

    if name:
        meal.name = name
    if description:
        meal.description = description
    if date:
        try:
            new_date = datetime.strptime(date, "%Y-%m-%d").date()
            meal.datetime = meal.datetime.replace(
                year  = new_date.year,
                month = new_date.month,
                day   = new_date.day
            )
        except ValueError:
            return jsonify({"message": "Formato de data e hora deve ser YYYY-MM-DD HH:MM:SS"}), 400      
    if time:
        try:
            new_time = datetime.strptime(time, "%H:%M:%S").time()
            meal.datetime = meal.datetime.replace(
                hour   = new_time.hour,
                minute = new_time.minute,
                second = new_time.second
            )
        except ValueError:
            return jsonify({"message": "Formato de data e hora deve ser YYYY-MM-DD HH:MM:SS"}), 400
    if diet:
        meal.diet = diet

    db.session.commit()

    return jsonify({"message": f"Refeição {id_meal} atualizada com sucesso"})

@app.route("/meal/<int:id_meal>", methods=["DELETE"])
@login_required
def delete_meal(id_meal):
    meal = Meal.query.get(id_meal)

    if not meal:
        return jsonify({"message": "Registro não encontrado"}), 404
    
    if current_user.id != meal.id_user and current_user.role == "user":
        return jsonify({"message": "Você não tem permissão para deletar esse registro"}), 403
    
    db.session.delete(meal)
    db.session.commit()

    return jsonify({"message": "Deleção realizada com sucesso"})
    
@app.route("/meals/<int:id_user>", methods=["GET"])
@login_required
def get_meals(id_user):
    user = User.query.get(id_user)

    if not user:
        return jsonify({"message": "Usuário não encontrado"}), 404
    if current_user.id != user.id and current_user.role == "user":
        return jsonify({"message": "Você não tem permissão para acessar essas informações"}), 403

    meal_list = []
    for meal in user.meal:
        meal_list.append({
            "id": meal.id,
            "name": meal.name,
            "description": meal.description,
            "datetime": meal.datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "diet": meal.diet
        })

    return jsonify({"meals": f"{meal_list}"})

@app.route("/meal/<int:id_meal>", methods=["GET"])
@login_required
def get_meal(id_meal):
    meal = Meal.query.filter_by(id=id_meal).first()

    if not meal:
        return jsonify({"message": "Registro não encontrado"}), 404
    if meal.id_user != current_user.id and current_user.role == "user":
        return jsonify({"message": "Você não tem permissão para acessar essas informações"}), 403

    return jsonify({
        "meal": {
            "id": meal.id,
            "name": meal.name,
            "description": meal.description,
            "datetime": meal.datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "diet": meal.diet
        }
    })

if __name__ == "__main__":
    app.run(debug=True)