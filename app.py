import pymongo
from flask import Flask, render_template, send_from_directory, Response
from markupsafe import escape
from waitress import serve

import utils

app = Flask("GUI Progetto")
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["ProgettoBD2"]


def main() -> None:
    debug = True  # TODO: cambia o rimuovi
    if debug:
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        serve(app, host='0.0.0.0', port=5000)


@app.route("/")
def serve_index() -> Response:
    return serve_html("index.html")


@app.route("/prova")
def serve_prova() -> str:
    food = db["food"]
    query = {"High": {"$gt": 50}}
    result = food.find(query)
    data = dict((record["_id"], record) for record in result)
    for key in data.keys():
        del data[key]["_id"]
    return render_template("prova.html", data=data)


@app.route("/<path>")
def serve_html(path: str) -> Response:
    if not path.endswith(".html"):
        path += ".html"
    return send_from_directory("templates", escape(path))


@app.get("/js/<path>")
def serve_js(path: str) -> Response:
    return send_from_directory("templates/js", escape(path))


@app.get("/css/<path>")
def serve_css(path: str) -> Response:
    return send_from_directory("templates/css", escape(path))


@app.get("/favicon.ico")
def serve_favicon() -> Response:
    return send_from_directory("templates", "favicon.ico", mimetype="image/vnd.microsoft.icon")


@app.errorhandler(404)
def page_not_found(e) -> (Response, int):
    return serve_html("404.html"), 404


if __name__ == "__main__":
    main()
