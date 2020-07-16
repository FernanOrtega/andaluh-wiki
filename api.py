from flask import Flask, redirect

flask_app = Flask(__name__)


ES_WIKI_ROOT = "https://es.wikipedia.org/"


@flask_app.route('/', defaults={'url_path': ''})
@flask_app.route('/<path:url_path>')
def get_request(url_path):
    target_url =  ES_WIKI_ROOT+url_path
    return redirect(target_url, code=302)


if __name__ == '__main__':
    flask_app.run(debug=False, host="0.0.0.0", port=5000)
