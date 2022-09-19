import sqlite3 as sql3
import pandas as pd
from markupsafe import escape
from flask import Flask, request, jsonify, url_for

app = Flask(__name__)


@app.route("/")
def home():
    pass


@app.route("/pokemons/", methods=["GET"])
def get_all_pokemons():
    pokemon_filters = request.args
    query = """SELECT PokemonID, PokedexNumber, PokemonName, AlternateFormName, t1.Type as "Pokemon Type 1", t2.Type as "Pokemon Type 2"
        FROM Pokemon
        left JOIN Types t1 ON PrimaryType == t1.RecordID 
        left JOIN Types t2 ON SecondaryType == t2.RecordID 
    """
    with sql3.connect("../pokeDB.db") as conn:
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        data = cur.fetchall()
        pokemon_list = [
            {
                "pokemonID":pokemon[0],
                "pokedex_number":pokemon[1],
                "pokemon_name":pokemon[2],
                "alternate_form_name":pokemon[3],
                "primary_type":pokemon[4],
                "secondary_type":pokemon[5]
             } 
            for pokemon in data
        ]
        results = {
                "count": len(pokemon_list),
                "data": pokemon_list                
        }
    return jsonify(results)


@app.route("/pokemons/<pokedex_ref>")
def get_pokemon_by_pokedex(pokedex_ref):
    try:        
        pokedex_ref = int(pokedex_ref)
        query_condition = f"WHERE PokedexNumber == {pokedex_ref}"
    except ValueError:
        print("test")
        pokemon_name = str(pokedex_ref).lower().capitalize()
        query_condition = f"WHERE PokemonName == \"{pokemon_name}\";"
    finally:
        query = f"""SELECT Pokemon.*,
         t1.Type as primary_type,
         t2.Type as secondary_type, 
         a1.Ability as primary_ability, 
         a1.description as primary_ability_description, 
         a2.Ability as secondary_ability, 
         a2.description as secondary_ability_description, 
         a3.Ability as hidden_ability,
         a3.description as hidden_ability_description, 
         "Region of Origin" as region_of_origin,
         e1."Egg Group" as primary_egg_group,
         e2."Egg Group" as secondary_egg_group,
         "Game(s) of Origin" as game_of_origin
        From Pokemon
            left JOIN Types t1 ON PrimaryType == t1.RecordID 
            left JOIN Types t2 ON SecondaryType == t2.RecordID 
            LEFT JOIN Abilities a1 on PrimaryAbility == a1.RecordID
            LEFT JOIN Abilities a2 on SecondaryAbility == a2.RecordID
            LEFT JOIN Abilities a3 on HiddenAbility == a3.RecordID
            LEFT JOIN Regions on RegionofOrigin == Regions.RecordID
            LEFT JOIN EggGroups e1 on PrimaryEggGroup == e1.RecordID
            LEFT JOIN EggGroups e2 on SecondaryEggGroup == e2.RecordID
            LEFT JOIN Games on GameofOrigin == Games.RecordID
        {query_condition}
    """
        with sql3.connect("../pokeDB.db") as conn:
            df = pd.read_sql(query, conn)
            df.drop(columns=["PrimaryType","SecondaryType","PrimaryAbility","SecondaryAbility", "HiddenAbility", "SpecialEventAbility", "RegionofOrigin", "GameofOrigin", "PrimaryEggGroup", "SecondaryEggGroup", ], inplace=True)
            df = df.to_dict()
            pokemon_data = {
                "id": df["PokemonID"][0],
                "Name":df["PokemonName"][0],
                "legendaryType": df["LegendaryType"][0],
                "originalPokemonID": df["OriginalPokemonID"][0],
                "alternateForm": df["AlternateFormName"][0],
                "legendaryType": df["LegendaryType"][0],
                "pokedexInfo":{
                    "pokedexNumber": df["PokedexNumber"][0],
                    "category": df["Classification"][0],
                    "height":df["PokemonHeight"][0],
                    "weight": df["PokemonWeight"][0],
                    "gameOfOrigin": df["game_of_origin"][0],
                    "regionOfOrigin": df["region_of_origin"][0],
                    "types": {
                        "primary":df["primary_type"][0],
                        "secondary":df["secondary_type"][0]    
                    },
                    "abilities": {
                        "primary": {
                            "ability": df["primary_ability"][0],
                            "description": df["primary_ability_description"][0]
                        },
                        "secondary": {
                            "ability": df["secondary_ability"][0],
                            "description": df["secondary_ability_description"][0]
                        },
                        "hidden": {
                            "ability": df["hidden_ability"][0],
                            "description": df["hidden_ability_description"][0]
                        },                  
                    }
                },               
                "training":{
                    "catchRate": df["CatchRate"][0],
                    "baseHappiness": df["BaseHappiness"][0],
                    "evolutionInfo": {
                        "previousEvolutionID": df["PreEvolutionPokemonId"][0],
                        "experienceGrowthTotal": df["ExperienceGrowthTotal"][0],
                        "evolutionDetails": df["EvolutionDetails"][0],
                        "experienceYield": df["EvolutionDetails"][0],
                    },
                    "evYield": {
                        "health": df["HealthEV"][0],
                        "attack": df["AttackEV"][0],
                        "defense": df["DefenseEV"][0],
                        "spAttack": df["SpecialAttackEV"][0],
                        "spDefense": df["SpecialDefenseEV"][0],
                        "speed": df["SpeedEV"][0],
                    },
                    "catchRate": df["CatchRate"][0],                    
                },
                "baseStats": {
                    "health": df["HealthStat"][0],
                    "attack": df["AttackStat"][0],
                    "defense": df["DefenseStat"][0],
                    "spAttack": df["SpecialAttackStat"][0],
                    "spDefense": df["SpecialDefenseStat"][0],
                    "speed": df["SpeedStat"][0],
                },
                "breeding":{
                    "eggCycleCount": df["EggCycleCount"][0],
                    "femaleRatio": df["FemaleRatio"][0],
                    "maleRatio": df["MaleRatio"][0],
                    "eggGroup": {
                        "primary": df["primary_egg_group"][0],
                        "secondary": df["secondary_egg_group"][0]
                    }
                },                
            }
        return pokemon_data


if __name__ == "__main__":
    app.run(debug=True)
