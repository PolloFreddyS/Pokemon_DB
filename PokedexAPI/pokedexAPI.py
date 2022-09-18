import sqlite3 as sql3
import json
import pandas as pd
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/pokemon/")
def pokedex_summary():
    query = """SELECT PokemonID, PokedexNumber, PokemonName, t1.Type as "Pokemon Type 1", t2.Type as "Pokemon Type 2"
        FROM Pokemon
        left JOIN Types t1 ON PrimaryType == t1.RecordID 
        left JOIN Types t2 ON SecondaryType == t2.RecordID 
    """
    with sql3.connect("../pokeDB.db") as conn:
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        data = cur.fetchall()
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
