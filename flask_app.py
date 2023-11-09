import requests
import time
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
db = SQLAlchemy(app)


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def create_nodes_class(table_name):
    class Nodes(db.Model):
        __tablename__ = f'{table_name}_nodes'
        id = db.Column(db.Integer, primary_key=True)
        keyword = db.Column(db.String, nullable=False)
        width = db.Column(db.Integer, nullable=False)
        height = db.Column(db.Integer, nullable=False)
        fontSize = db.Column(db.Integer, nullable=False)
        color = db.Column(db.String, nullable=False)
        __table_args__ = {'extend_existing': True}

    with app.app_context():
        db.create_all()

    return Nodes

def create_edges_class(table_name):
    class Edges(db.Model):
        __tablename__ = f'{table_name}_edges'
        id = db.Column(db.Integer, primary_key=True)
        source = db.Column(db.String, nullable=False)
        target = db.Column(db.String, nullable=False)
        __table_args__ = {'extend_existing': True}

    with app.app_context():
        db.create_all()

    return Edges

def add_node_row(class_name, keyword, width, height, fontSize, color):
    engine = create_engine('sqlite:///database.db')
    metadata = MetaData()
    metadata.reflect(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    node = class_name(keyword=keyword, width=width, height=height, fontSize=fontSize, color=color)
    session.add(node)
    session.commit()

def add_edge_row(class_name, source, target):
    engine = create_engine('sqlite:///database.db')
    metadata = MetaData()
    metadata.reflect(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    node = class_name(source=source, target=target)
    session.add(node)
    session.commit()

def searchGoogle(keyword):
    url = f'https://www.google.com/search?q={keyword}'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    # soup html을 .html파일로 저장
    # with open('test.html', 'w') as f:
    #     f.write(soup.prettify())

    relKeyword = soup.select('.gGQDvd.iIWm4b')
    print(f'{keyword}의 연관 검색어 검색중... {len(relKeyword)}개 검색 완료')
    time.sleep(1)
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
            'width' :  lv * 5,
            'height' : lv * 5,
            'fontSize' : lv * 4,
            'color' : f'hsla(163, 100%, {30 / lv}%, 1)'
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


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])


def search():
    engine = create_engine('sqlite:///database.db')
    metadata = MetaData()
    metadata.reflect(bind=engine)

    keyword = request.form.get('keyword').strip()
    lv = int(request.form.get('lv').strip())
    # lv이 3 이상이면 3로 고정
    # if lv > 3:
        # lv = 3

    table_name = f'{keyword}_{lv}'
    all_table_names = metadata.tables.keys()
    
    print(all_table_names)
    if any(all_table_name.startswith(table_name) for all_table_name in all_table_names):
        print(f"해당 테이블이 존재합니다. : '{table_name}'")
        nodes = []
        edges = []
        for node in create_nodes_class(table_name).query.all():
            nodes.append({
                'id' : node.keyword,
                'width' : node.width,
                'height' : node.height,
                'fontSize' : node.fontSize,
                'color' : node.color,
            })
        for edge in create_edges_class(table_name).query.all():
            edges.append({
                'source' : edge.source,
                'target' : edge.target,
            })
        return render_template('map.html', keyword=keyword, nodes=nodes, edges=edges)
    else:
        print(f"해당 테이블이 없습니다. : '{table_name}'")
        relKeyword = searchGoogle(keyword)
        nodes = [
            {
                'id' : keyword,
                'width' : 30,
                'height' : 30,
                'fontSize' : 20,
                'color' : 'hsla(163, 100%, 10%, 1)',
            }
        ]
        edges = []

        process_keywords(relKeyword, lv, nodes, edges, keyword)

        for node in nodes:
            add_node_row(create_nodes_class(table_name), node['id'], node['width'], node['height'], node['fontSize'], node['color'])    

        for edge in edges:
            add_edge_row(create_edges_class(table_name), edge['source'], edge['target'])    

        return render_template('map.html', keyword=keyword, nodes=nodes, edges=edges)

if __name__ == '__main__':
    app.run(debug=True)