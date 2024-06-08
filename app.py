import pymongo
from flask import Flask, render_template, send_from_directory, Response
from markupsafe import escape

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


@app.get('/js/<path>')
def serve_js(path: str) -> Response:
    return send_from_directory('static/js', escape(path))


@app.get('/css/<path>')
def serve_css(path: str) -> Response:
    return send_from_directory('static/css', escape(path))


@app.get('/favicon.ico')
def serve_favicon() -> Response:
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.errorhandler(404)
def page_not_found(e) -> Response:
    return send_from_directory('static', '404.html')


if __name__ == '__main__':
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['ProgettoBD2']

    food = db['food']
    global_dataset = db['global_dataset']
    global_inflation = db['global_inflation']
    us_cpi = db['consumer_price_index']

    app.run(host='0.0.0.0', port=5000, debug=True)
