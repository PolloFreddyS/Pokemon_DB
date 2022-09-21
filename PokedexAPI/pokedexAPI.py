from pprint import pprint
import sqlite3 as sql3
import pandas as pd
from flasgger import Swagger
from markupsafe import escape
from flask import Flask, request, jsonify, url_for, abort

app = Flask(__name__)
swagger = Swagger(app)

@app.route("/")
def home():
    pass


@app.route("/pokemons/", methods=["GET"])
def get_all_pokemons():
    pokemon_filters = request.args
    type_filters = pokemon_filters.getlist("type",)
    region_filter = pokemon_filters.get("region",)
    game_filter = pokemon_filters.get("game",)
    egg_groups = pokemon_filters.getlist("eggGroup")
    ability_filter = pokemon_filters.get("ability")
    if len(pokemon_filters) == 0:   # If no filter arg is given, returns the whole list of pokemons
        query = """SELECT PokemonID, PokedexNumber, PokemonName, AlternateFormName, t1.RecordID as "primaryTypeId", t1.Type as "Pokemon Type 1", t2.RecordID as "secondaryTypeId", t2.Type as "Pokemon Type 2"
            FROM Pokemon
            left JOIN Types t1 ON PrimaryType == t1.RecordID 
            left JOIN Types t2 ON SecondaryType == t2.RecordID 
        """
    else:
        query_conditions = []                   # initialize query conditions list
        if type_filters:
            pprint("here")
            if len(type_filters)==2:                # if 2 types are selected
                types_condition = []                # initialize the conditional statement for the query
                alternate_types_condition = []      # initialize the alternative conditional statement for the query
                for pokemon_type in type_filters:   # to check alternate type order
                    try:                            # try to convert the args to integer to find pokemons by their type ID
                        types_condition.append(f"t1.RecordID == {int(pokemon_type)}")   # append condition to the list of conditions
                        alternate_types_condition.append(f"t2.RecordID == {int(pokemon_type)}") # and the alternate form
                    except ValueError:
                        pokemon_type = pokemon_type.capitalize()
                        types_condition.append(f"t1.Type == \"{pokemon_type}\"")    # If the args could not be converted to integers
                        alternate_types_condition.append(f"t2.Type == \"{pokemon_type}\"")  # Do the query with the pokemon type string
                final_types_conditions = f"(({types_condition[0]} AND {alternate_types_condition[1]}) \
                    OR ({types_condition[1]} AND {alternate_types_condition[0]}) )"
                query_conditions.append(f"({final_types_conditions})")      # Appending the resulting condition statement to the list of conditions for the query
            
            elif len(type_filters)==1:         
                pokemon_type = type_filters[0]
                try:
                    # If a single type is given as a filter, try to convert it to int so an ID is used to find
                    # pokemons of that type.
                    query_conditions.append(f"(t1.RecordID == {int(pokemon_type)} OR t2.RecordID == {int(pokemon_type)})")                
                except ValueError:
                    pokemon_type = pokemon_type.capitalize()
                    # If it can't be converted to integer, then try to find it directly with its type.
                    query_conditions.append(f"(t1.Type == \"{pokemon_type}\" OR t2.Type == \"{pokemon_type}\")")
            elif len(type_filters)>2:
                abort(400, "Pokemons can only have 2 types")

        # Do the same with the Egg groups and abilities
        if egg_groups:
            if len(egg_groups)==2:
                eggs_condition = []
                alternate_eggs_condition = []
                for egg_type in egg_groups:
                    try:
                        eggs_condition.append(f"eggGroupID_1 == {int(egg_type)}")
                        alternate_eggs_condition.append(f"eggGroupID_2 == {int(egg_type)}")
                    except ValueError:
                        egg_type = egg_type.capitalize
                        eggs_condition.append(f"primaryEggGroup == \"{egg_type}\"")
                        alternate_eggs_condition.append(f"secondaryEggGroup == \"{egg_type}\"")
                final_eggs_conditions = f"(({eggs_condition[0]} AND {alternate_eggs_condition[1]}) \
                    OR ({eggs_condition[1]} AND {alternate_eggs_condition[0]}) )"
                query_conditions.append(f"({final_eggs_conditions})")
            
            elif len(egg_groups)==1:
                egg_groups = egg_groups[0].capitalize()
                try:
                    query_conditions.append(f"(eggGroupID_1 == {int(egg_groups)} OR eggGroupID_2 == {int(egg_groups)})")                
                except ValueError:
                    query_conditions.append(f"(primaryEggGroup, == \"{egg_groups}\" OR secondaryEggGroup == \"{egg_groups}\")")
            
            elif len(egg_groups)>2:
                abort(400,)
        
        if ability_filter:
            if len(ability_filter)>1:
                abort(400)
            elif len(ability_filter)==1:
                try:
                    query_conditions.append(f"(AbilityId_1 == {int(ability_filter)} OR AbilityId_2 == {int(ability_filter)} OR AbilityId_3 == {int(ability_filter)})")
                except ValueError:
                    ability_filter = ability_filter.capitalize()
                    query_conditions.append(f"(primaryAbility == \"{ability_filter}\" OR secondaryAbility == \"{ability_filter}\" OR hiddenAbility == \"{ability_filter}\")")
            
            if region_filter:
                try:
                    # Do the same with the region filters.
                    query_conditions.append(f"(regionID == {int(region_filter)})")
                except ValueError:
                    query_conditions.append(f"(Region == \"{region_filter.capitalize()}\")")
                    
            if game_filter:
                try:
                    # Do the same with the game filters.
                    query_conditions.append(f"(gameID == {int(game_filter)})")
                except ValueError:
                    query_conditions.append(f"(gameOfOrigin == \"{game_filter.capitalize()}\")")
        
        query_conditions = " AND ".join(query_conditions)
                            
        query = f"""SELECT PokemonID, PokedexNumber, PokemonName, AlternateFormName, t1.RecordID as "primaryTypeId", t1.Type as "Pokemon Type 1",
t2.RecordID as "secondaryTypeId", t2.Type as "Pokemon Type 2", Regions."Region of Origin" as Region, Regions.RecordID as regionID,
Games."Game(s) of Origin" as gameOfOrigin, Games.RecordID as gameID, e1.RecordID as eggGroupID_1, e1."Egg Group" as primaryEggGroup,
e2.RecordID as eggGroupID_2, e2."Egg Group" as secondEggGroup, a1.Ability as primaryAbility, a1.RecordID as AbilityId_1, a1.description as primaryAbilityDescription, 
a2.Ability as secondaryAbility, a2.RecordID as AbilityId_2, a2.description as secondaryAbilityDescription, a3.Ability as hiddenAbility, 
a3.RecordID as AbilityId_3, a3.description as hiddenAbilityDescription   
            FROM Pokemon
             LEFT JOIN Types t1 ON PrimaryType == t1.RecordID 
             LEFT JOIN Types t2 ON SecondaryType == t2.RecordID
             LEFT JOIN Regions  ON RegionofOrigin == Regions.RecordID
             LEFT JOIN Abilities a1 ON PrimaryAbility == a1.RecordID
             LEFT JOIN Abilities a2 ON SecondaryAbility == a2.RecordID
             LEFT JOIN Abilities a3 ON HiddenAbility == a3.RecordID
             LEFT JOIN EggGroups e1 ON PrimaryEggGroup == e1.RecordID
             LEFT JOIN EggGroups e2 ON SecondaryEggGroup == e2.RecordID
             LEFT JOIN Games ON GameofOrigin == Games.RecordID
            WHERE {query_conditions}
        """
        
    with sql3.connect("../pokeDB.db") as conn:
        cur = conn.cursor()
        # cur.execute(query)
        # conn.commit()
        # data = cur.fetchall()
        df = pd.read_sql(query, conn)
        # pokemon_list = [
        #     {
        #         "pokemonID":pokemon[0],
        #         "pokedex_number":pokemon[1],
        #         "pokemon_name":pokemon[2],
        #         "alternate_form_name":pokemon[3],
        #         "primary_type":pokemon[4],
        #         "secondary_type":pokemon[5]
        #      } 
        #     for pokemon in df
        # ]
        # results = {
        #         "count": len(pokemon_list),
        #         "data": pokemon_list                
        # }
    return jsonify(df.to_dict())


@app.route("/pokemons/<pokedex_ref>")
def get_pokemon_by_pokedex(pokedex_ref):
    pprint(request.args.getlist("asd"))
    try:        
        pokedex_ref = int(pokedex_ref)
        query_condition = f"WHERE PokedexNumber == {pokedex_ref}"
    except ValueError:
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
            if len(df) < 1:
                abort(404, "No pokemon found with that reference")
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
