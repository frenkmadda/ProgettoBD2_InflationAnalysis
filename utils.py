def query_print_all(collection, query):
    results = collection.find(query)
    for entry in results:
        print(entry)


def query_print_parameter(collection, my_query, param):
    results = collection.find(my_query)
    for entry in results:
        print(entry[param])


def query_print_one(collection, query):
    result = collection.find_one(query)
    print(result.next())


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
