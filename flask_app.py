import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keyword').strip()
    url = f'https://www.google.com/search?q={keyword}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    relKeyword = soup.select('.gGQDvd.iIWm4b')
    nodes = []
    edges = []
    for rel in relKeyword:
        nodes.append(rel.text.strip())
        edges.append({
            'source'  : rel.text.strip(),
            'target'  : keyword
        })

    return render_template('map.html', keyword=keyword, nodes=nodes, edges=edges)

if __name__ == '__main__':
    app.run(debug=True)

