from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta, datetime    
import sqlite3
import hashlib
import database, admin
from game import game as card_game
conn = sqlite3.connect("main.db",check_same_thread=False)
c = conn.cursor()

app = Flask(__name__)
app.secret_key = "something to say about nothing"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(minutes=5)

addresses = {}

def hash(str):
    salt = "2d1133dd810c6ca8e84118c79545847b"
    hashed = hashlib.md5(str.encode()+salt.encode())
    return hashed.hexdigest()

def get_redirect():
    if "redirect" not in session:
        session["redirect"] = None

    if session["redirect"] is not None:
        redirect = session["redirect"]
        session["redirect"] = None
        return url_for(redirect)
    return None

#-------------------------------------webpage functions------------------------------------------

@app.route("/")
@app.route("/home/")
def home():
    global addresses
    session["address"] = request.remote_addr
    addresses[session["address"]] = None
    url = get_redirect()
    if url is not None:
        return redirect(url)
    if "username" in session and "password" in session:
        return render_template("/user/home.html", values=[session["username"],session["password"]]) 
    return redirect(url_for("login"))

@app.route("/create_user/",methods=["POST","GET"])
def create_user():
    if "username" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        if request.form["create_user"] == "yes":
            print(session["username"],session["password"])
            c.execute("INSERT INTO users VALUES (:username, :password, :score, :role)",
            {"username":session["username"],"password":session["password"], "score":database.default_score, "role":database.default_role})
            conn.commit()
            session["role"] = database.default_role
            return redirect(url_for('home'))
        if request.form["create_user"] == "no":
            return redirect(url_for("logout"))
    return render_template("user/create_user.html")

@app.route("/login/", methods=["POST","GET"])
def login():
    if request.method == "POST":
        username = request.form["name"]
        password = hash(request.form["password"])
        c.execute("SELECT role FROM users WHERE username =:username AND password =:password",
        {"username":username,"password":password})
        session["username"] = username
        session["password"] = password
        output = c.fetchall()
        if len(output) == 0:
            return redirect(url_for("create_user"))
        session["role"] = output[0][0]
        return redirect(url_for("home"))

    return render_template("user/login.html")

@app.route("/logout/")
def logout():
    to_del = dict(session)
    for x in to_del:
        session.pop(x)
    return redirect(url_for("home"))

#---------------------------------user-----------------------------------------

@app.route("/user/")
def user_home():
    return redirect(url_for("user_update"))

@app.route("/user/update")
def user_update():
    return render_template("/user/update/home.html")

@app.route("/user/update/password", methods=["POST","GET"])
def user_update_password():
    if "username" not in session:
        session["redirect"] = "user_update_password"
        return redirect(url_for("login"))
    if request.method == "POST":
        if "current" not in request.form:
            return render_template("/user/update/password.html",message="")

        if hash(request.form["current"]) == session["password"]:
            c.execute("UPDATE users SET password=:new_password WHERE username =:username and password =:password",{
                "new_password":hash(request.form["new1"]), "password":session["password"],"username":session["username"] 
            })
            conn.commit()
            session["password"] = hash(request.form["new1"])
            return redirect(url_for("home"))
        else:
            return render_template("/user/update/password.html",message="Entered Current Password Is Incorrect")  
    return render_template("/user/update/password.html")


@app.route("/user/update/role", methods=["POST","GET"])
def user_update_role():
    if "username" not in session:
        session["redirect"] = "user_update_role"
        return redirect(url_for("login"))
    if request.method == "POST":
        c.execute("UPDATE users SET role=:new_role WHERE username =:username and password =:password",{
            "new_role":request.form["role"], "password":session["password"],"username":session["username"] 
        })
        conn.commit()
        session["password"] = hash(request.form["role"])
        return redirect(url_for("home"))
    return render_template("/user/update/role.html", values=admin.roles)

#---------------------------------users----------------------------------------

@app.route("/users/")
def users():
    return render_template("/users/home.html")

@app.route("/users/view/")
def users_view():
    c.execute("SELECT * FROM users")
    conn.commit()
    return render_template("/users/view.html", values=c.fetchall())

@app.route("/users/delete/", methods=["POST","GET"])
def users_delete():
    if "username" not in session:
        session["redirect"] = "users_delete"
        return redirect(url_for("login"))
    if session["role"] in admin.admin_roles:
        return redirect(url_for("users_delete_admin"))
    if request.method == "POST":
        if request.form["answer"] == "yes":
            c.execute("DELETE FROM users WHERE username=:username AND password=:password",{
                "username":session["username"], "password":session["password"]
            })
            conn.commit()
            return redirect(url_for("logout"))
        return redirect(url_for("home"))
    return render_template("/user/delete/user.html")

@app.route("/users/delete/admin/", methods=["POST","GET"])
def users_delete_admin():
    if "username" not in session:
        session["redirect"] = "users_delete_admin"
        return redirect(url_for("login"))
    if session["role"] not in admin.admin_roles:
        return redirect(url_for("users_delete"))
    if request.method == "POST":
        username, password = request.form["del_user"].split("¦|")
        c.execute("DELETE FROM users WHERE username=:username AND password=:password",
        {"username":username,"password":password})
        conn.commit()
        return redirect(url_for("users_view"))
    c.execute("SELECT * FROM users")
    conn.commit()
    return render_template("/user/delete/admin.html",values=c.fetchall())

#---------------------------------game-------------------------------------------

@app.route("/game/")
def game_home():
    if "address" not in session or session["address"] not in addresses: 
        session["redirect"] = "game_home"
        return redirect(url_for("home"))
    if "username" not in session:
        session["redirect"] = "game_home"
        return redirect(url_for("login"))
    addresses[session["address"]] = card_game()
    session["write_winner"] = False
    url = get_redirect()
    if url is not None:
        return redirect(url)
    return render_template("/game/home.html")

@app.route("/game/playing/<value>")
def game_playing(value):
    global addresses
    if "address" not in session or session["address"] not in addresses:
        session["redirect"] = "game_home"
        return redirect(url_for("home"))
    
    if addresses[session["address"]] is None:
        return redirect(url_for("game_home"))
    
    if not value.isdigit():
        return redirect(url_for("game_playing", id="1"))
    
    session["id"] = int(value)-1
    if session["id"] > len(addresses[session["address"]].output_vals)-1 or session["id"] < 0:
        return redirect(url_for("game_home"))

    session["left_card"], session["right_card"], session["winner"] = addresses[session["address"]].output_vals[session["id"]]
    session["left_colour"], session["left_number"] = session["left_card"]
    session["right_colour"], session["right_number"] = session["right_card"]
    session["last_card"] = False
    if session["id"] == len(addresses[session["address"]].output_vals)-1:
        session["last_card"] = True
        if not session["write_winner"]:
            c.execute("SELECT score FROM users WHERE username=:username AND password=:password",{
                "username":session["username"], "password":session["password"]
            })
            session["old_score"] = c.fetchall()[0][0]
            session["new_score"] = int(addresses[session["address"]].final_cards_per_player[0])/int(len(addresses[session["address"]].output_vals))*100
            if float(session["old_score"]) < float(session["new_score"]):
                c.execute("UPDATE users SET score=:new_score WHERE username =:username and password =:password",{
                "new_score":session["new_score"], "password":session["password"],"username":session["username"] 
                })
                conn.commit()
            session["write_winner"] = True
    return render_template("/game/playing.html", left_colour=session["left_colour"], right_colour=session["right_colour"], left_number=session["left_number"], right_number=session["right_number"], id=int(session["id"]), winner=session["winner"], last_card=session["last_card"])

@app.route("/game/finnished/")
def game_finnished():
    if "address" not in session or session["address"] not in addresses:
        session["redirect"] = "game_finnished"
        return redirect(url_for("game_home"))
    session["p_cards_vals"] = addresses[session["address"]].final_cards
    session["p_cards"] = addresses[session["address"]].final_cards_per_player
    if session["p_cards"][0] > session["p_cards"][1]:
        session["winner"] = "Player 1"
    else:
        session["winner"] = "Player 2"
    return render_template("/game/finnished.html", winner=session["winner"],p1_cards=session["p_cards"][0],p2_cards=session["p_cards"][1], p_cards=session["p_cards_vals"])

@app.route("/game/scoreboard/")
def game_scoreboard():
    if "username" not in session:
        session["redirect"] = "game_scoreboard"
        return redirect(url_for("login"))

    c.execute("SELECT * FROM users ORDER BY score DESC")
    conn.commit()
    session["players"] = c.fetchall()
    if len(session["players"]) > admin.max_players_on_leaderboard:
        session["players"] = session["players"][:admin.max_players_on_leaderboard]
    return render_template("/game/score.html", players=session["players"])

@app.route("/game/view/")
def game_view():
    if "address" not in session or session["address"] not in addresses:
        session["redirect"] = "game_view"
        return redirect(url_for("home"))
    if addresses[session["address"]] is None:
        return redirect(url_for("game_home"))
    return render_template("/game/view.html", values=addresses[session["address"]].output_vals)
#---------------------------databases--------------------------------------------

@app.route("/database/")
def database_home():
    return render_template("/database/home.html")

@app.route("/database/setup/")
def database_setup():
    try:
        c.execute("""
        CREATE TABLE users(
            username characters(100),
            password characters(100),
            score characters(10),
            role characters(25))""")
        conn.commit()
        return redirect(url_for("home"))
    except:
        return "<p>Table exists</p><br><a href='/'>Home</a>"

@app.route("/database/clear/", methods=["post","get"])
def database_clear():
    if request.method == "POST":
        if request.form["answer"] in admin.yes_ans:
            if session["role"] in admin.admin_roles:
                c.execute("DELETE FROM users")
                conn.commit()
                return redirect(url_for("logout"))

    if "username" not in session:
        session["redirect"] = "database_clear"
        return redirect(url_for("login"))
    
    return render_template("/database/clear.html")

if __name__ == "__main__":
    app.run(debug=True)
    #app.run(host="0.0.0.0")