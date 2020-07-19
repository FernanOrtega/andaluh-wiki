import requests
from bs4 import BeautifulSoup, Comment
from flask import Flask, request, Response
import andaluh
import json

ROOT_DOMAIN = "https://es.wikipedia.org/"
WKP_CT_SUMMARY_API = 'application/json; charset=utf-8; profile="https://www.mediawiki.org/wiki/Specs/Summary/1.4.2"'
WKP_CT_HTML = 'text/html; charset=UTF-8'
WKP_SUMMARY_API_KEYS_2_TRANSC = ["title", "displaytitle", "description", "extract", "extract_html"]
WKP_HTML_TAGS_2_TRANS = ["span", "h1", "h2", "h3", "h4", "h5"]
WKP_HTML_TAGS_2_TRANS_WITH_CH = ["p", "th"]


flask_app = Flask(__name__)


def transcribe(text, vaf='ç', vvf='h'):
    transcription = andaluh.epa(text, vaf=vaf, vvf=vvf)
    return transcription


def transcribe_elem_text(elem, vaf, vvf):
    if hasattr(elem, "string") and elem.string and not isinstance(elem.string, Comment):
        elem.string.replaceWith(transcribe(elem.string, vaf=vaf, vvf=vvf))

    if hasattr(elem, "children"):
        for ch in elem.children:
            if not isinstance(ch, Comment):
                transcribe_elem_text(ch, vaf, vvf)


def transcribe_html(html_content, vaf="ç", vvf="h"):
    soup = BeautifulSoup(html_content, "lxml")

    # for tag in WKP_HTML_TAGS_2_TRANS:
    #     for elem in soup.find_all(tag):
    #         if elem.string:
    #             elem.string.replaceWith(transcribe(elem.string, vaf=vaf, vvf=vvf))
    #
    # for tag in WKP_HTML_TAGS_2_TRANS_WITH_CH:
    #     for elem_parent in soup.find_all(tag):
    #         for ch in elem_parent.children:
    #             if ch.string:
    #                 ch.string.replaceWith(transcribe(ch.string, vaf=vaf))

    transcribe_elem_text(soup.body, vaf=vaf, vvf=vvf)

    return str(soup)


def prepare_content(req):
    if req.headers.get("Content-Type") == WKP_CT_SUMMARY_API:
        content_dict = json.loads(req.content)

        for key in WKP_SUMMARY_API_KEYS_2_TRANSC:
            if key is "extract_html":
                content_dict[key] = transcribe(content_dict[key])
            content_dict[key] = transcribe(content_dict[key])

        content = json.dumps(content_dict, ensure_ascii=False).encode("utf-8")
    elif req.headers.get("Content-Type") == WKP_CT_HTML:
        content = transcribe_html(req.content.decode("utf-8")).encode("utf-8")
    else:
        content = req.content

    return content


@flask_app.route('/', defaults={'url_path': ''})
@flask_app.route('/<path:url_path>', methods=["GET", "POST"])
def get_request(url_path):
    target_url = ROOT_DOMAIN + url_path
    http_method = requests.post if request.method == 'POST' else requests.get

    if request.query_string:
        query_string_decoded = request.query_string.decode("utf-8")
        target_url = f"{target_url}?{query_string_decoded}"
        req = http_method(target_url)
    elif request.json:
        data = request.json
        req = http_method(target_url, json=data)

    elif request.form:
        data = request.form.to_dict()
        req = http_method(target_url, data=data)
    else:
        req = http_method(target_url)

    content = prepare_content(req)
    return Response(content, content_type=req.headers.get("Content-Type"))


if __name__ == '__main__':
    flask_app.run(debug=True, host="0.0.0.0", port=5000)
