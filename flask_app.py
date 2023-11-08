import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def searchGoogle(keyword):
    url = f'https://www.google.com/search?q={keyword}'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    # soup html을 .html파일로 저장
    # with open('test.html', 'w') as f:
    #     f.write(soup.prettify())

    relKeyword = soup.select('.gGQDvd.iIWm4b')
    print(f'{keyword}의 연관 검색어 검색중... {len(relKeyword)}개 검색 완료')
    return relKeyword

searched_keywords = set()
def process_keywords(relKeywords, lv, nodes, edges, keyword=None):
    if not relKeywords:
        return

    for rel in relKeywords:
        rel_text = rel.text.strip()
        if rel_text in searched_keywords:
            continue
        searched_keywords.add(rel_text)
        nodes.append({
            'id' : rel_text,
            'width' : 5 - abs(lv - 1),
            'height' : 5 - abs(lv - 1),
            'fontSize' : 4 - abs(lv - 1),
            'color' : f'hsla(163, 100%, {20 + (10 * abs(lv - 1))}%, 1)',
        })
        if keyword:
            edges.append({
                'source'  : rel_text,
                'target'  : keyword
            })
        if lv > 1:
            relKeyword = searchGoogle(rel_text)
            if relKeyword:
                process_keywords(relKeyword, lv-1, nodes, edges, rel_text)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])

def search():
    keyword = request.form.get('keyword').strip()
    lv = int(request.form.get('lv').strip())
    # lv이 5 이상이면 3으로 고정
    if lv > 5:
        lv = 5

    relKeyword = searchGoogle(keyword)
    nodes = [
        {
            'id' : keyword,
            'width' : 10,
            'height' : 10,
            'fontSize' : 5,
            'color' : 'hsla(163, 100%, 10%, 1)',
        }
    ]
    edges = []

    process_keywords(relKeyword, lv, nodes, edges, keyword)

    return render_template('map.html', keyword=keyword, nodes=nodes, edges=edges)

if __name__ == '__main__':
    app.run(debug=True)