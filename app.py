from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from pkg_resources import require
import requests, json, random
import pandas as pd
import plotly
import plotly.express as px

app = Flask(__name__)
db = SQLAlchemy(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

class Voters(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    voted_for = db.Column(db.String(10))

@app.route("/sign_in", methods=["GET", "POST"])
def sign_in():
    global name, email
    name = request.form.get("name")
    email = request.form.get("email")

    if (name and email):
        return render_template("voting.html")
    else:
        return render_template("sign_in.html")

@app.route("/voting", methods=["GET", "POST"])
def voting():
    voted_for = request.form.get("option", False)
    print(voted_for, "-------------------------------")

    new_voter = Voters(name=name, email=email, voted_for=voted_for)
    db.session.add(new_voter)
    db.session.commit()

    return redirect(url_for("result"))

@app.route("/update/<string:type>")
def update(type):
    base_url = "https://pokeapi.co/api/v2/type/"
    required_url = base_url + type

    #getting pokemon url
    pokemon_url_response = requests.get(required_url)
    poke_url_dict = random.choice(pokemon_url_response.json()["pokemon"])
    poke_url = poke_url_dict["pokemon"]["url"]
    print("POKE URL "+poke_url)

    #getting pokemon image url reponse
    pokemon_image_response = requests.get(poke_url)
    poke_img = pokemon_image_response.json()["sprites"]["versions"]["generation-vii"]["ultra-sun-ultra-moon"]["front_default"]
    print(poke_img)

    poke_fire_img, poke_water_img, poke_grass_img = "", "", ""
    if type == "fire":
        poke_fire_img = poke_img
    elif type == "water":
        poke_water_img = poke_img
    else:
        poke_grass_img = poke_img
    
    return render_template("voting.html", poke_fire_img=poke_fire_img, poke_water_img=poke_water_img, poke_grass_img=poke_grass_img)

@app.route("/result")
def result():
    fire_votes = len(db.session.query(Voters).filter(Voters.voted_for == "fire").all())
    water_votes = len(db.session.query(Voters).filter(Voters.voted_for == "water").all())
    grass_votes = len(db.session.query(Voters).filter(Voters.voted_for == "grass").all())

    print(fire_votes, water_votes, grass_votes)

    return render_template("result.html", fire_votes=fire_votes, water_votes=water_votes, grass_votes=grass_votes)

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)