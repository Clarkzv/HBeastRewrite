from flask import Flask, jsonify, render_template, request, redirect, url_for
import requests
import secrets
import json
from fake_useragent import UserAgent
import os

app = Flask(__name__)

def logger(ip_addr, request_url):
    token = os.environ.get("TOKEN")
    chat = os.environ.get("CHAT")
    ip_log_url = f"http://ip-api.com/json/{ip_addr}"
    data = {"url": request_url, "ip_data": requests.get(ip_log_url).json()}
    post_url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat}&text={json.dumps(data)}"
    try:
        requests.get(post_url)
    except requests.RequestException as e:
        print(f"Error sending log: {e}")
    return "logged!"

def get_json(url, headers=None):
    headers = headers or {}
    headers = {"X-Signature-Version": "web2","X-Signature": secrets.token_hex(32),'User-Agent': UserAgent().random}
    response = requests.get(url, headers=headers)
    return response.json()

def get_trending(time, page):
    url = f"https://hanime.tv/api/v8/browse-trending?time={time}&page={page}&order_by=views&ordering=desc"
    data = get_json(url)
    return [{"id": x['id'], "name": x['name'], "slug": x['slug'], "url": f"/video/{x['slug']}", "cover_url": x['cover_url'], "views": x['views"], "link": f"/api/video/{x['slug']}"} for x in data["hentai_videos"]]

def get_video(slug):
    url = f"https://hanime.tv/api/v8/video?id={slug}"
    data = get_json(url)
    tags = [{"name": t['text'], "link": f"/browse/hentai-tags/{t['text']}/0"} for t in data['hentai_tags']]
    streams = [{"width": s['width'], "height": s['height'], "size_mbs": s['filesize_mbs'], "url": s['url'], "link": s['url']} for s in data['videos_manifest']['servers'][0]['streams']]
    episodes = [{"id": e['id'], "name": e['name'], "slug": e['slug'], "cover_url": e['cover_url'], "views": e['views'], "link": f"/api/video/{e['slug']}"} for e in data['hentai_franchise_hentai_videos']]
    video = {"id": data["hentai_video"]["id"], "name": data["hentai_video"]["name"], "description": data["hentai_video"]["description"], "poster_url": data["hentai_video"]["poster_url"], "cover_url": data["hentai_video"]["cover_url"], "views": data["hentai_video"]["views"], "streams": streams, "tags": tags, "episodes": episodes}
    return [video]

def get_browse():
    url = "https://hanime.tv/api/v8/browse"
    data = get_json(url)
    return data

def get_browse_videos(type, category, page):
    url = f"https://hanime.tv/api/v8/browse/{type}/{category}?page={page}&order_by=views&ordering=desc"
    data = get_json(url)
    return [{"id": x['id'], "name": x['name'], "slug": x['slug'], "cover_url": x['cover_url'], "views": x['views'], "link": f"/api/video/{x['slug']}"} for x in data["hentai_videos"]]

def get_search(query, page):
    res = {"search_text": query, "tags": [], "brands": [], "blacklist": [], "order_by": [], "ordering": [], "page": page}
    headers = {"Content-Type": "application/json; charset=utf-8"}
    response = requests.post("https://search.htv-services.com", headers=headers, json=res)
    data = response.json()
    videos = data['hits']
    total_pages = data['nbPages']
    return [{"id": x['id'], "name": x['name'], "slug": x['slug'], "url": f"/video/{x['slug']}", "cover_url": x['cover_url'], "views": x['views'], "link": f"/api/video/{x['slug']}"} for x in videos], total_pages

@app.route('/')
def index():
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)
    return redirect(url_for('trending_page', time='month', page=0))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form['search_query']
        redirect_url = url_for('search', query=search_query, page=0)
        return redirect(redirect_url)

    query = request.args.get('query')
    page = int(request.args.get('page', 0))
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)

    videos, total_pages = get_search(query, page)
    next_page = url_for('search', query=query, page=page + 1) if page < total_pages - 1 else None

    return render_template('search.html', videos=videos, next_page=next_page, query=query)

@app.route('/api')
def api():
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)
    return render_template('api.html')

@app.route('/trending/<time>/<int:page>')
def trending_page(time, page):
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)
    videos = get_trending(time, page)
    next_page = url_for('trending_page', time=time, page=page + 1)
    return render_template('trending.html', videos=videos, next_page=next_page, time=time)

@app.route('/video/<slug>')
def video_page(slug):
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)
    video = get_video(slug)[0]
    return render_template('video.html', video=video)

@app.route('/play')
def m3u8():
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)
    link = request.args.get('link')
    return render_template('play.html', link=link)

@app.route('/browse')
def browse():
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)
    data = get_browse()
    return render_template('browse.html', tags=data['hentai_tags'])

@app.route('/browse/<type>/<category>/<int:page>')
def browse_category(type, category, page):
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)
    videos = get_browse_videos(type, category, page)
    data = get_browse()
    next_page = url_for('browse_category', type=type, category=category, page=page + 1)
    return render_template('cards.html', videos=videos, next_page=next_page, category=category, tags=data['hentai_tags'])

@app.route('/api/video/<slug>')
def video_api(slug):
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)
    data = get_video(slug)
    return jsonify({'results': data}), 200

@app.route('/api/trending/<time>/<int:page>')
def trending_api(time, page):
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)
    data = get_trending(time, page)
    next_page = url_for('trending_api', time=time, page=page + 1, _external=True)
    return jsonify({'results': data, 'next_page': next_page}), 200

@app.route('/api/browse/<type>')
def browse_type_api(type):
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)
    data = get_browse()[type]
    if type == 'hentai_tags':
        for x in data:
            x['url'] = f"/api/browse/hentai-tags/{x['text']}/0"
    elif type == 'brands':
        for x in data:
            x['url'] = f"/api/browse/brands/{x['slug']}/0"
    return jsonify({'results': data}), 200

@app.route('/api/browse')
def browse_api():
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)
    return jsonify({'tags': '/api/browse/hentai_tags', 'brands': '/api/browse/brands'}), 200

@app.route('/api/browse/<type>/<category>/<int:page>')
def browse_category_api(type, category, page):
    ip_addr = request.remote_addr
    request_url = request.url
    logger(ip_addr, request_url)
    data, total_pages = get_browse_videos(type, category, page)
    next_page = url_for('browse_category_api', type=type, category=category, page=page + 1, _external=True) if page < total_pages - 1 else None
    return jsonify({'results': data, 'next_page': next_page}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
