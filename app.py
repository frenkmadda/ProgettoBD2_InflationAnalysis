import json
from html import escape

import plotly
import plotly.graph_objs as go
import pycountry
import pymongo
from flask import Flask, render_template, send_from_directory, Response, request

import utils

app = Flask('GUI Progetto')
app.jinja_env.add_extension('jinja2.ext.loopcontrols')  # Aggiunge funzioni extra ai cicli, come il break


@app.route('/')
def serve_index() -> str:
    return render_template('index.html')


@app.route('/prova')
def serve_prova() -> str:
    query = {'High': {'$gt': 50}}
    result = food.find(query)
    data = dict((record['_id'], record) for record in result)
    for key in data.keys():
        del data[key]['_id']
    return render_template('prova.html', data=data)


@app.route('/inflation-by-country', methods=['GET', 'POST'])
def serve_ibc() -> str:
    if request.method == 'POST':
        country = request.form['country']
        inflation_values, years = utils.get_inflation_by_country(global_inflation, country)
        # Creazione del grafico
        data = [
            go.Scatter(
                x=inflation_values,
                y=years,
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
        country = None
        output = {}

        country_max_infl = global_inflation.find_one({"_id": documents[0]['_id']})
        country = country_max_infl['country_name']
        inflation_value = country_max_infl[year]
        ccode = get_ccode(country)

        return render_template('max-inflation.html', inflation_value=inflation_value, country=country, year=year, ccode=ccode)
    else:
        return render_template('max-inflation.html')


@app.route('/mean', methods=['GET', 'POST'])
def serve_mean() -> str:
    if request.method == 'POST':
        country = request.form['country']
        inflation_value = utils.get_avg_infl_years(global_inflation, country).next()['avgInflation']
        ccode = get_ccode(country)
        return render_template('mean.html', countries=countries, inflation_value=round(inflation_value,2), paese=country, ccode=ccode)
    else:
        return render_template('mean.html', countries=countries, inflation_value=None)


@app.route('/eu')
def serve_eu() -> str:
    query = {"Country Code": {
        "$in": ["AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "IRL", "ITA",
                "LVA", "LTU", "LUX", "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE"]}}
    eu = global_dataset.distinct('Country', query)
    result = utils.get_food_inflation_eur_per_year(global_dataset, eu)
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

    graph_json = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('eu.html', graphJSON=graph_json)


@app.get('/js/<path>')
def serve_js(path: str) -> Response:
    return send_from_directory('static/js', escape(path))


@app.get('/css/<path>')
def serve_css(path: str) -> Response:
    return send_from_directory('static/css', escape(path))


@app.get('/favicon.png')
def serve_favicon() -> Response:
    return send_from_directory('static', 'logo.png', mimetype='image/png')


@app.errorhandler(404)
def page_not_found(e) -> Response:
    return send_from_directory('static', '404.html')


def get_ccode(country: str):
    try:
        return pycountry.countries.search_fuzzy(country)[0].alpha_2
    except LookupError:
        return None


if __name__ == '__main__':
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['ProgettoBD2']

    food = db['food']
    global_dataset = db['global_dataset']
    global_inflation = db['global_inflation']
    us_cpi = db['consumer_price_index']

    countries = global_inflation.distinct('country_name')
    app.run(host='0.0.0.0', port=5000, debug=True)
