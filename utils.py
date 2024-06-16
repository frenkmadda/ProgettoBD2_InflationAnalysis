from bson.objectid import ObjectId


def get_max_infl_year(collection, anno):
    """
    Estrae il paese che ha l'inflazione maggiore dato un anno.

    :param collection: La Collection di MongoDB
    :param anno:       L'anno da cercare
    :return:           Un cursore che contiene il Documento MongoDB
    """
    anno = int(anno)
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


def get_avg_infl_eur(collection, european_countries):
    """
    Estrae l'inflazione dei paesi dell'UE eliminando le categorie e accorpando
    le 5 categorie in unico valore calcolato con una media tra i 5.

    :param collection:            La Collection di MongoDB
    :param european_countries:
    :return:
    """
    years = [str(year) for year in range(1970, 2025)]

    pipeline = [
        # Filtro per i paesi europei
        {"$match": {"Country": {"$in": european_countries}}},
        # Raggruppamento per paese e calcolo della media per ogni anno
        {"$group": {
            "_id": "$Country",
            **{year: {"$avg": f"${year}"} for year in years}
        }}
    ]

    result = collection.aggregate(pipeline)

    return result


def get_food_inflation_eur_per_year(collection, europeanCountriesList):
    """
    Estrae e fa una media del tasso di inflazione nel campo alimentare negli anni.

    :param collection:
    :param europeanCountriesList:
    :return:
    """
    years = [str(year) for year in range(1970, 2023)]

    pipeline = [
        # Filtro per i documenti con "Series Name" = "Food Consumer Price Inflation"
        {"$match": {"Series Name": "Food Consumer Price Inflation"}},
        # Raggruppamento per anno e calcolo della media per ogni anno
        {"$group": {
            "_id": None,
            **{year: {"$avg": f"${year}"} for year in years}
        }}
    ]

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


def get_inflation_by_country(dataset, country_name):
    """
    Estrae gli anni e i valori di inflazione per il paese specificato.
    :param dataset: Dataset global_inflation
    :param country_name: Nome del paese
    :return: anni e valori di inflazione
    """
    country_data = dataset.find_one({"country_name": country_name})

    # Rimozione dei campi non necessari
    country_data.pop('_id')
    country_data.pop('country_name')
    country_data.pop('indicator_name')

    # Estrazione degli anni e dei valori di inflazione
    years = list(country_data.keys())
    inflation_values = list(country_data.values())

    return years, inflation_values


def insert_into_collection(collection, country_name, inflation_value, year):
    """
    Inserisce un documento in una Collection di MongoDB.
    :param collection: La collection mongoDB
    :param country_name: Il nome del paese da inserire
    :param inflation_value: Il valore dell'inflazione da inserire
    :param year: L'anno da inserire
    :return: ritorna il cursor del documento inserito
    """
    if year not in range(1980, 2025):
        raise ValueError("L'anno deve essere compreso tra il 1980 e il 2024!")

    if collection.name == "global_inflation":
        param = "country_name"
    elif collection.name == "global_dataset":
        param = "Country"
    elif collection.name == "food":
        param = "country"
    else:
        raise ValueError("La collection non è valida")

    document = {
        param: country_name,
        "inflation_value": inflation_value,
        "year": year
    }

    result = collection.insert_one(document)
    return result.inserted_id


def delete_document(collection, doc_id):
    """
    Cancella un documento da una collection
    :param collection: La collection MongoDB
    :param doc_id: L'id del documento da cancellare
    :return: Il risultato dell'operazione
    """
    query = {"_id": ObjectId(doc_id)}
    result = collection.delete_one(query)
    return result


def find_by_id(collection, doc_id):
    """
    Trova un documento in una collection dato il suo id
    :param collection: La collection MongoDB
    :param doc_id: L'id del documento da cercare
    :return: il risultato dell'operazione come cursore
    """
    query = {"_id": ObjectId(doc_id)}
    result = collection.find_one(query)

    return result


def update_document(collection, doc_id, document):
    """
    Aggiorna un documento in una collection
    :param collection: La collection MongoDB
    :param doc_id: L'id del documento da aggiornare
    :param document: Il documento con i nuovi valori
    :return: Il risultato dell'operazione
    """
    query = {"_id": ObjectId(doc_id)}
    new_values = {"$set": document}
    result = collection.update_one(query, new_values)
    return result


def integration_food(food, global_dataset):
    """
    Funzione per integrare i dati di food con global dataset.
    Vengono formattati i dati di food, precedemente aventi un documento per ogni mese in
    documenti divisi per anno e paese. Formattati 'Country', 'Year', 'infl'
    Vengono poi identificati i paesi mancanti in global dataset che saranno integrati da food.
    La differenza nella formattazione dei documenti può creare fastidio nei plot, il problema è
    stato gestito in seguito.

    :param food: la collection food di MongoDB
    :param global_dataset: la collection di global dataset di MongoDB
    :return: ritorna il cursore alla lista di documenti integrati
    """
    pipeline = [
        {
            "$addFields": {
                "year": {"$year": "$date"},  # Estrai l'anno dalla data
            }
        },
        {
            "$group": {
                "_id": {"country": "$country", "year": "$year"},  # Raggruppa per country e year
                "inflationSum": {"$sum": "$Inflation"},  # Somma i valori di inflation
            }
        },
        {
            "$project": {
                "_id": 0,
                "country": "$_id.country",
                "year": "$_id.year",
                "Inflation": "$inflationSum",
            }
        },
    ]
    grouped_data = list(food.aggregate(pipeline))
    country_codes = global_dataset.distinct("Country Code")
    food_country_list = food.distinct("country")

    result = list(get_eu_food_infl_countries(global_dataset, country_codes))
    grouped_data_dict = {(doc['country'], doc['year']): doc.get('Inflation', 0) for doc in grouped_data if
                         'country' in doc and 'year' in doc}
    existing_countries = [doc['Country'] for doc in result]

    for doc in result:
        doc.pop('_id')
        doc.pop('Indicator Type')
        doc.pop('Note')

    for country in food_country_list:
        if country not in existing_countries:
            for year in range(1980, 2025):
                infl = grouped_data_dict.get((country, year))
                if infl is not None:
                    result.append({
                        'country': country,
                        'year': year,
                        'infl': infl
                    })

    return result


def format_data(grouped_data, documents_with_infl):
    """
    Formatta i dati per l'operazione di plotting rimuovendo i campo non necessari e formattando
    i documenti in modo che contengano l'anno e il valore di inflazione in ogni documento.
    I documenti di global dataset erano formati da un campo 'Country' e un campo per
    ogni anno con associato il valore di inflazione.
    Nei dati di food il campo 'country' viene rinominato in 'Country'
    per uniformità con gli altri documenti.

    :param grouped_data: i dati integrati di food e global dataset
    :param documents_with_infl: i documenti di food per gestire la formattazione
    :return: Una nuova lista di documenti formattata come 'Country', 'Year', 'infl'
    """

    grouped_data_year = []

    # Itera attraverso gli anni nel documento originale
    for doc in grouped_data:
        for year in range(1996, 2023):
            if str(year) in doc:
                infl_value = doc[str(year)]
            else:
                infl_value = None
            new_doc = {
                "Year": year,
                "infl": infl_value,
                "Country Code": doc["Country Code"],
                "Country": doc["Country"],
                "Series Name": doc["Series Name"],
            }
            grouped_data_year.append(new_doc)

    for doc in documents_with_infl:
        doc['Country'] = doc.pop('country')

    for doc in documents_with_infl:
        grouped_data_year.append(doc)

    return grouped_data_year


def get_food_inflation_by_country(grouped_data_year, country):
    """
    Estrae l'inflazione alimentare di un paese per anno data una lista di documenti previamente
    formattati per l'operazione
    :param grouped_data_year: La lista di documenti formattati
    :param country: Il paese di cui si vuole estrarre l'inflazione
    :return: Gli anni e i valori di inflazione
    """
    country_data = [doc for doc in grouped_data_year if doc['Country'] == country]

    years = [doc['Year'] for doc in country_data]
    inflation_values = [doc['infl'] for doc in country_data]

    return years, inflation_values


def plot_food_inflation_by_country(collection_food, collection_global_dataset, country):
    """
    Pipeline di funzioni utile alla web app per plottare l'inflazione alimentare di un paese
    integrando i dati di food e global_dataset
    :param collection_food: la colletion Food di Mongodb
    :param collection_global_dataset: la collection GlobalDataset di Mongodb
    :param country: Il paese di cui si vuole plottare l'inflazione
    :return: gli anni e i dati dell'inflazione
    """

    grouped_data = integration_food(collection_food, collection_global_dataset)

    documents_with_infl = [doc for doc in grouped_data if 'infl' in doc]
    grouped_data = [doc for doc in grouped_data if 'infl' not in doc]

    grouped_data_year = format_data(grouped_data, documents_with_infl)

    years, inflation_values = get_food_inflation_by_country(grouped_data_year, country)

    return years, inflation_values
