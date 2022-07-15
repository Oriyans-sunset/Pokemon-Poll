from crypt import methods
from distutils.util import change_root
from flask import Flask, redirect, render_template, request, url_for, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from pkg_resources import require
import requests, json, random
import pandas as pd
import plotly
import plotly.express as px

app = Flask(__name__)
db = SQLAlchemy(app)

app.secret_key = "abc"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#setting up Voter database
class Voters(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    voted_for = db.Column(db.String(10))

@app.route("/sign-in", methods=["GET"])
def showSignInPage():
    return render_template("sign_in.html")

@app.route("/sign-in", methods=["POST"])
def showVotingPage():

    #using sessions to provide access to the voting() func
    name = request.form.get("name")
    email = request.form.get("email")

    session["name"] = name
    session["email"] = email

    return render_template("voting.html")

@app.route("/voting", methods=["GET", "POST"])
def voting():
    """
    Desc: Updates the database with information
    Paramaters: N/A
    """

    voted_for = request.form.get("option", False)

    try:
        new_voter = Voters(name=session["name"], email=session["email"], voted_for=voted_for)
    except KeyError:
        return redirect(url_for("showSignInPage"))

    db.session.add(new_voter)
    db.session.commit()

    session["id"] = new_voter.id

    return redirect(url_for("result"))

@app.route("/update/<string:type>")
def update(type):
    """
    Desc: Updates the image for that particular pokemon card
    Paramaters: type("fire", "water", "grass")
    """

    #adding "type" parameter to base url fetches list of all pokemon of that type
    base_url = "https://pokeapi.co/api/v2/type/"
    required_url = base_url + type

    #getting pokemon url for a specific pokemon
    pokemon_url_response = requests.get(required_url)
    poke_url_dict = random.choice(pokemon_url_response.json()["pokemon"])
    poke_url = poke_url_dict["pokemon"]["url"]

    #getting pokemon image url using pokemon url acquired above 
    pokemon_image_response = requests.get(poke_url)
    poke_img = pokemon_image_response.json()["sprites"]["versions"]["generation-vii"]["ultra-sun-ultra-moon"]["front_default"]

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
    """
    Desc: Displays summary statistics for the poll
    Paramaters: N/A
    """

    fire_votes = len(db.session.query(Voters).filter(Voters.voted_for == "fire").all())
    water_votes = len(db.session.query(Voters).filter(Voters.voted_for == "water").all())
    grass_votes = len(db.session.query(Voters).filter(Voters.voted_for == "grass").all())

    return render_template("result.html", fire_votes=fire_votes, water_votes=water_votes, grass_votes=grass_votes, voter_id = session["id"])

@app.route("/delete-vote/<int:id>", methods=["GET", "DELETE"])
def delete_vote(id):
    Voters.query.filter_by(id=id).delete()
    db.session.commit()

    return redirect(url_for("result"))

@app.route("/update-vote/<int:id>", methods=["GET"])
def showUpdate_votePage(id):
    return render_template("update_vote.html", voter_id = session["id"])

@app.route("/update-vote/<int:id>", methods=["POST", "PUT"])
def updateVote(id):

    #issue unresolved: when a vote is deleted, update vote funtion does work because the ID is also delted ong wiht the previous vote
    changed_vote = request.form.get("type")

    if (Voters.query.get(id)):
        prev_vote = Voters.query.filter_by(id=id).update({Voters.voted_for: changed_vote}, synchronize_session = False)
    else:
        new_voter = Voters(name=session["name"], email=session["email"], voted_for=changed_vote)
        db.session.add(new_voter)
    
    db.session.commit()

    return redirect(url_for("result"))

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)