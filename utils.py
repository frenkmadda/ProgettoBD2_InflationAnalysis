def query_print_all(collection, query):
    results = collection.find(query)
    for entry in results:
        print(entry)

    return results


def query_print_parameter(collection, my_query, param):
    results = collection.find(my_query)
    for entry in results:
        print(entry[param])
    return results

def query_print_one(collection, query):
    result = collection.find_one(query)
    print(result.next())

    return result

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


def get_food_inflation_eur(db, europeanCountriesList):
    # Creazione dell'array con gli anni di interesse
    years = [str(year) for year in range(2002, 2023)]

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
    result = db.aggregate(pipeline)

    # Creazione del dizionario per l'output
    output = {}

    # Riempimento del dizionario con i risultati
    for doc in result:
        doc.pop('_id')  # Rimuove la chiave '_id' non necessaria
        output.update(doc)

    return output


def get_eu_food_infl(collection, country_list):
    """
    Estrae la media, tra gli anni 1980 e 2024, dell'inflazione dei paesi dell'Unione Europea.

    :param collection: La Collection di MongoDB
    :param country_list: La lista delle sigle dei paesi dell'Unione Europea
    :return:           Un cursore che contiene il Documento MongoDB
    """

    query = {
        "Country Code": {"$in": country_list},
        "Series Name": "Food Consumer Price Inflation"
    }
    result = collection.find(query)

    # Stampa dei risultati
    for doc in result:
        print(doc)

    return result



