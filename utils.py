def get_max_infl_year(collection, anno):
    """
    Estrae il paese che ha l'inflazione maggiore dato un anno.

    :param collection: La Collection di MongoDB
    :param anno:       L'anno da cercare
    :return:           Un cursore che contiene il Documento MongoDB
    """
    if anno < 1980 or anno > 2024:
        raise ValueError("L'anno deve essere compreso tra il 1980 e il 2024!")

    return collection.aggregate([
        {"$project": {"country": 1, str(anno): 1}},
        {"$sort": {str(anno): -1}},
        {"$limit": 1}
    ])


def get_avg_infl_years(collection, country):
    """
    Estrae la media, tra gli anni 1980 e 2024, dell'inflazione di un dato paese.

    :param collection: La Collection di MongoDB
    :param country:    Il nome in inglese della Nazione
    :return:           Un cursore che contiene il Documento MongoDB
    """
    anni = [str(a) for a in range(1980, 2025)]
    return collection.aggregate([
        {"$match": {"country_name": country}},
        {"$project": {
            "country": 1,
            "avgInflation": {"$avg": [f"${a}" for a in anni]}
        }}
    ])


def get_avg_infl_eur(collection, europeanCountriesList):
    """
    Estrae l'inflazione dei paesi dell'UE eliminando le categorie e accorpando
    le 5 categorie in unico valore calcolato con una media tra i 5.

    :param collection:            La Collection di MongoDB
    :param europeanCountriesList:
    :return:
    """
    # Creazione dell'array con gli anni di interesse
    years = [str(year) for year in range(1970, 2025)]

    # Creazione del pipeline di aggregazione
    pipeline = [
        # Filtro per i paesi europei
        {"$match": {"Country": {"$in": europeanCountriesList}}},
        # Raggruppamento per paese e calcolo della media per ogni anno
        {"$group": {
            "_id": "$Country",
            **{year: {"$avg": f"${year}"} for year in years}
        }}
    ]

    # Esecuzione dell'aggregazione
    result = collection.aggregate(pipeline)

    return result


def get_food_inflation_eur_per_year(collection, europeanCountriesList):
    """
    Estrae e fa una media del tasso di inflazione nel campo alimentare negli anni.

    :param db:
    :param europeanCountriesList:
    :return:
    """
    # Creazione dell'array con gli anni di interesse
    years = [str(year) for year in range(1970, 2023)]

    # Creazione del pipeline di aggregazione
    pipeline = [
        # Filtro per i documenti con "Series Name" = "Food Consumer Price Inflation"
        {"$match": {"Series Name": "Food Consumer Price Inflation"}},
        # Raggruppamento per anno e calcolo della media per ogni anno
        {"$group": {
            "_id": None,
            **{year: {"$avg": f"${year}"} for year in years}
        }}
    ]

    # Esecuzione dell'aggregazione
    result = collection.aggregate(pipeline)

    return result


def get_eu_food_infl_countries(collection, country_list):
    """
    Estrae il tasso di inflazione nel campo alimentare dei paesi Europei.

    :param collection:   La Collection di MongoDB
    :param country_list: La lista delle sigle dei paesi dell'Unione Europea
    :return:             Un cursore che contiene i Documenti MongoDB
    """

    query = {
        "Country Code": {"$in": country_list},
        "Series Name": "Food Consumer Price Inflation"
    }
    result = collection.find(query)

    return result
