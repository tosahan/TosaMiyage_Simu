from flask import *
from flask_httpauth import *
from flask_sqlalchemy import *
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kochi_osake.db"
app.config["SQLALCHEMY_BINDS"] = {
    "otsumami": "sqlite:///kochi_otsumami.db"
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# auth = HTTPBasicAuth()

class Kochi_osake(db.Model):
    __tablename__ = "kochi_osake"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255)) # product's name
    kinds = db.Column(db.String(255), nullable=True) # kinds of sake
    price = db.Column(db.Integer) # price of product
    url = db.Column(db.String(255))

class Kochi_otsumami(db.Model):
    __bind_key__ = "otsumami"
    __tablename__ = "kochi_otsumami"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255)) # product's name
    price = db.Column(db.Integer) # price of product
    url = db.Column(db.String(255))

# @auth.get_password
# def get_pw(username):
#     if username in users:
#         return users.get(username)
#     return None

# ホームページ
@app.route("/")
def index():
    # data = Kochi_osake.query.all()
    return render_template("index.html")

# お酒追加画面
# 管理者限定(予定)
@app.route("/add_sake", methods=["GET", "POST"])
def add_sake():
    if request.method == "POST":
        name = request.form["name"]
        kinds = request.form.get("kinds", "")
        price = request.form["price"]
        new_product = Kochi_osake(name=name, kinds=kinds, price=price)
        db.session.add(new_product)
        db.session.commit()
        data = Kochi_osake.query.all()
        return render_template("add_sake.html", data=data)
    data = Kochi_osake.query.all()
    return render_template("add_sake.html", data=data)

# 酒管理画面での削除メソッド
@app.route("/del_sake/<int:id>")
def del_sake(id):
    del_data = Kochi_osake.query.filter_by(id=id).first()
    if del_data:
        db.session.delete(del_data)
        db.session.commit()
    return redirect(url_for("index"))

# おつまみ追加画面
@app.route("/add_otsumami", methods=["GET", "POST"])
def add_otsumami():
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        new_product = Kochi_otsumami(name=name, price=price)
        db.session.add(new_product)
        db.session.commit()
        data = Kochi_otsumami.query.all()
        return render_template("add_otsumami.html", data=data)
    data = Kochi_otsumami.query.all()
    return render_template("add_otsumami.html", data=data)

# おつまみ管理画面での削除メソッド
@app.route("/del_otsumami/<int:id>")
def del_otsumami(id):
    del_data = Kochi_otsumami.query.filter_by(id=id).first()
    if del_data:
        db.session.delete(del_data)
        db.session.commit()
    return redirect(url_for("index"))

# 予算と酒の本数の入力画面
@app.route("/choose_budget", methods=["GET", "POST"])
def choose_budget():
    if request.method == "POST":
        budget = request.form.get("budget")
        sakenum = request.form.get("sakenum")
        redirect_url = url_for("gacha_home", budget=budget, sakenum=sakenum)
        # print(f"Redirecting to: {redirect_url}")
        return redirect(redirect_url)
    return render_template("choose_budget.html")

# ガチャのホーム画面
@app.route("/gacha_home")
def gacha_home():
    budget = request.args.get("budget", "予算が選択されていません")
    sakenum = request.args.get("sakenum", "酒の本数が選択されていません")
    # print(f"Budget on gacha_home: {budget}, Sakenum: {sakenum}")
    return render_template("gacha_home.html", budget=budget, sakenum=sakenum)

# ガチャの実行とその結果の表示
@app.route("/gacha_result")
def gacha():
    budget = int(request.args.get("budget", 0))
    sakenum = int(request.args.get("sakenum", 0))
    # print(f"Budget: {budget}, Sakenum: {sakenum}") # ok

    orisakes = Kochi_osake.query.all()
    sakes = [(sake.name, sake.price) for sake in orisakes]
    oriotsumamies = Kochi_otsumami.query.all()
    otsumamies = [(otsumami.name, otsumami.price) for otsumami in oriotsumamies]
    # print("sakes: ", sakes)
    # print("otsumamies: ", otsumamies)
    # ok

    # 予算内で決められた本数の酒を選ぶ
    selected_items = []
    total_price = 0
    while len(selected_items) < sakenum and sakes:
        sake = random.choice(sakes)
        sake_name, sake_price = sake
        if total_price + sake_price <= budget:
            selected_items.append(sake)
            total_price += sake_price
            sakes.remove(sake)
    if len(selected_items) < sakenum:
        flash("この予算ではお酒が購入できません", "error")
        return redirect(url_for("gacha_home"))
    
    print("sake's total price = ", total_price) # ok
    budget -= total_price
    print("remained budget = ", budget) # ok

    if selected_items is None:
        flash("この予算ではお酒が購入できません", "error")
        return redirect(url_for("gacha_home"))
    else:
        # 残りの予算でおつまみを最大化する(重複あり)
        dp = [0] * (budget + 1)
        count = [[] for _ in range(budget + 1)]
        
        for otsumami_name, otsumami_price in otsumamies:
            for x in range(otsumami_price, budget + 1):
                if dp[x - otsumami_price] + otsumami_price > dp[x]:
                    dp[x] = dp[x - otsumami_price] + otsumami_price
                    count[x] = count[x - otsumami_price] + [(otsumami_name, otsumami_price)]

        # 結果を表示するためのコード
        best_count = count[budget]
        
        # ページに返す
        return render_template("gacha_result.html", item=selected_items, otsumamis=best_count)


# ランダムな商品の表示
# for debug
# @app.route("/random")
# def get_random():
#     random_sake = Kochi_osake.query.order_by(db.func.random()).first()
#     return render_template("random.html", sake=random_sake)

# @auth.login_required
# def hello():
#     return "Hello,world!"

# @app.route("/index")
# def index():
#     return "Hello, %s!" % auth.username()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)