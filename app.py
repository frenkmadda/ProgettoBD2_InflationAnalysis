import json
from html import escape

import plotly
import plotly.graph_objs as go
import pycountry
import pymongo
from flask import Flask, render_template, send_from_directory, Response, request
from pymongo.collection import Collection

import utils

app = Flask('GUI Progetto')
app.jinja_env.add_extension('jinja2.ext.loopcontrols')  # Aggiunge funzioni extra ai cicli di Flask, come il break


@app.get('/')
def serve_index() -> str:
    return render_template('index.html')


@app.get('/crud/read')
def serve_default_crud_view() -> (str, int):
    return serve_crud('food')


@app.get('/crud/read/<collection_name>')
def serve_crud(collection_name: str) -> (str, int):
    collection = get_collection_by_name(escape(collection_name))
    if collection is None:
        return bad_request('Errore nella lettura della Collection')

    result = collection.find({})
    data = dict((record['_id'], record) for record in result)
    for key in data.keys():
        del data[key]['_id']
    return render_template('crud.html', data=data, collection=collection_name), 200


@app.get('/crud/create')
def serve_create() -> (str, int):
    collection_name = request.args.get('collection', default='')
    collection = get_collection_by_name(collection_name)
    if collection is None:
        return bad_request('Errore nella lettura della Collection')

    return render_template('create.html', collection_name=collection_name), 200


@app.post('/crud/create')
def create_document() -> (str, int):
    collection_name = request.args.get('collection', default='')
    country = request.args.get('country_name', default='')
    inflation = request.args.get('inflation_value', default='')
    year = request.args.get('year', default='')
    collection = get_collection_by_name(collection_name)

    if collection is None or country == '' or inflation == '' or year == '':
        return bad_request('Errore nella lettura dei dati')

    if country == 'Sbiriguda':
        return send_from_directory('static', 'easter-egg.html')

    utils.insert_into_collection(get_collection_by_name(collection_name), country, float(inflation), int(year))
    return serve_crud(collection_name)


@app.get('/crud/update')
def serve_update() -> (str, int):
    document_id = request.args.get('id', default='')
    collection_name = request.args.get('collection', default='')
    collection = get_collection_by_name(collection_name)
    if collection is None:
        return bad_request('Errore nella lettura della Collection')

    doc = utils.find_by_id(get_collection_by_name(collection_name), document_id)
    if doc is None:
        return bad_request('Errore nella lettura del documento')

    return render_template('update.html', document=doc, collection=collection_name), 200


@app.post('/crud/update')
def update_document() -> (str, int):
    data = dict(request.get_json())
    print(data)
    if data is None:
        return bad_request('Errore nella lettura dei dati')

    collection_name = data.get('collection')
    document_id = data.get('_id')
    del data['_id']
    del data['collection']

    if collection_name is None or document_id is None or data == {}:
        return bad_request('Errore nella lettura dei dati')

    collection = get_collection_by_name(collection_name)
    if collection is None:
        return bad_request('Errore nella lettura della Collection')

    utils.update_document(collection, document_id, data)
    return serve_crud(collection_name)


@app.get('/crud/delete')
def delete_document() -> (str, int):
    document_id = request.args.get('id', default='')
    collection_name = request.args.get('collection', default='')
    collection = get_collection_by_name(collection_name)
    if collection is None:
        return bad_request('Errore nella lettura della Collection')

    utils.delete_document(collection, document_id)
    return serve_crud(collection_name)


@app.route('/inflation-by-country', methods=['GET', 'POST'])
def serve_ibc() -> str:
    if request.method == 'POST':
        country = request.form['country']
        years, inflation_values = utils.get_inflation_by_country(global_inflation, country)
        # Creazione del grafico
        data = [
            go.Scatter(
                x=years,
                y=inflation_values,
                mode='lines+markers',
                name='Inflazione annuale'
            )
        ]

        ccode = get_ccode(country)
        graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('inflation-by-country.html', countries=countries, graphJSON=graph_json,
                               paese=country, ccode=ccode)
    else:
        return render_template('inflation-by-country.html', countries=countries, graphJSON='null')


@app.route('/max-inflation', methods=['GET', 'POST'])
def serve_max_inflation() -> str:
    if request.method == 'POST':
        year = request.form['year']
        result = utils.get_max_infl_year(global_inflation, year)
        documents = list(result)

        country_max_infl = global_inflation.find_one({"_id": documents[0]['_id']})
        country = country_max_infl['country_name']
        inflation_value = country_max_infl[year]
        ccode = get_ccode(country)

        years, inflation_values = utils.get_inflation_by_country(global_inflation, country)
        # Creazione del grafico
        data = [
            go.Scatter(
                x=years,
                y=inflation_values,
                mode='lines+markers',
                name='Inflazione annuale'
            )
        ]
        graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('max-inflation.html', inflation_value=inflation_value, country=country,
                               year=year, graphJson=graph_json, ccode=ccode)
    else:
        return render_template('max-inflation.html')


@app.route('/mean', methods=['GET', 'POST'])
def serve_mean() -> str:
    if request.method == 'POST':
        country = request.form['country']
        inflation_value = utils.get_avg_infl_years(global_inflation, country).next()['avgInflation']
        ccode = get_ccode(country)

        min_infl, max_infl = utils.get_min_max_inflation(global_inflation, country)
        return render_template('mean.html', countries=countries, inflation_value=round(inflation_value, 2),
                               paese=country, ccode=ccode, min_infl=min_infl, max_infl=max_infl)
    else:
        return render_template('mean.html', countries=countries, inflation_value=None)


@app.route('/food-infl', methods=['GET', 'POST'])
def serve_food_infl() -> str:
    if request.method == 'POST':
        country = request.form['country']
        years, inflation_values = utils.plot_food_inflation_by_country(food, global_dataset, country)
        data = [
            go.Scatter(
                x=years,
                y=inflation_values,
                mode='lines+markers',
                name='Inflazione annuale'
            )
        ]
        graph = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

        ccode = get_ccode(country)
        return render_template('food-infl.html', graph=graph, countries=countries, paese=country, ccode=ccode)
    else:
        return render_template('food-infl.html', countries=countries)


@app.get('/eu-g7')
def serve_eu_g7() -> str:
    query = {"Country Code": {
        "$in": ["AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "IRL", "ITA",
                "LVA", "LTU", "LUX", "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE"]}}
    eu = global_dataset.distinct('Country', query)
    result = utils.get_food_inflation_list_per_year(global_dataset, eu)
    output = {}

    # Riempimento del dizionario con i risultati
    for doc in result:
        doc.pop('_id')  # Rimuove la chiave '_id' non necessaria
        output.update(doc)

    anni = list(output.keys())
    inflazione = list(output.values())

    # Creazione del grafico
    data = [
        go.Scatter(
            x=anni,
            y=inflazione,
            mode='lines+markers',
            name='Inflazione annuale'
        )
    ]

    eu_graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    query = {"Country Code": {"$in": ["FRA", "DEU", "ITA", "USA", "CAN", "JPN", "GBR"]}}
    g7 = global_dataset.distinct('Country', query)
    result = utils.get_food_inflation_list_per_year(global_dataset, g7)
    output = {}
    for doc in result:
        doc.pop('_id')
        output.update(doc)

    anni = list(output.keys())
    inflazione = list(output.values())
    data = [
        go.Scatter(
            x=anni,
            y=inflazione,
            mode='lines+markers',
            name='Inflazione annuale'
        )
    ]
    g7_graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('eu-g7.html', euGraphJSON=eu_graph_json, g7GraphJSON=g7_graph_json)


@app.get('/js/<path>')
def serve_js(path: str) -> Response:
    return send_from_directory('static/js', escape(path))


@app.get('/css/<path>')
def serve_css(path: str) -> Response:
    return send_from_directory('static/css', escape(path))


@app.get('/img/<path>')
def serve_imgs(path: str) -> Response:
    return send_from_directory('static/img', escape(path), mimetype='image/jpg')


@app.get('/favicon.png')
def serve_favicon() -> Response:
    return send_from_directory('static', 'logo.png', mimetype='image/png')


@app.errorhandler(404)
def page_not_found(e) -> (Response, int):
    return send_from_directory('static', '404.html'), 404


def bad_request(message: str) -> (str, int):
    return render_template('error.html', message=message), 400


def get_ccode(country: str):
    try:
        return pycountry.countries.search_fuzzy(country)[0].alpha_2.lower()
    except LookupError:
        return None


def get_collection_by_name(collection_name: str) -> Collection | None:
    if collection_name == 'global_inflation':
        return global_inflation
    elif collection_name == 'food':
        return food
    elif collection_name == 'global_dataset':
        return global_dataset
    else:
        return None


def get_crud_data(collection_name: str) -> dict | None:
    collection = get_collection_by_name(collection_name)
    if collection is None:
        return None

    result = collection.find({})
    data = dict((record['_id'], record) for record in result)
    for key in data.keys():
        del data[key]['_id']
    return data


if __name__ == '__main__':
    print('Connessione al database in corso…')
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['ProgettoBD2']

    food = db['food']
    global_dataset = db['global_dataset']
    global_inflation = db['global_inflation']

    countries = global_inflation.distinct('country_name')
    print("Connesso. Avvio dell'app in corso…")
    app.run(host='0.0.0.0', port=5000)
