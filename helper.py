import requests
from bs4 import BeautifulSoup
import json
from pprint import pprint
from datetime import datetime

def getSoup(link):
    req = requests.get(link)
    html = req.content
    soup = BeautifulSoup(html, "html.parser")
    return soup

def get_all_products():
    product_links = {}
    product_links["links"] = []
    link = "https://rnm.franceagrimer.fr/prix?FRUITS-ET-LEGUMES"
    soup = getSoup(link)
    products = soup.findAll("div", {"class": "listunproduit"})
    for product in products:
        link = "https://rnm.franceagrimer.fr" + product.find("a")['href']
        product_links["links"].append(link)
    with open("product_links.json", "w") as f:
        json.dump(product_links,f)

def get_product_type(link):
    soup = getSoup(link)
    soup = soup.find("table", {"class": "tabcot"})
    rows = soup.findAll("tr")
    dets = []
    for row in rows:
        onclick = row.find("td", {"class": "tdcotl"})
        if not onclick == None:
            det = {}
            det = onclick.find("a")
            link = det['onclick'][10:-4]
            name = det.text
            det['name'] = name.strip()
            det['link'] = link
            dets.append(det)
    return dets

def get_type_dets(libcod):
    information = []
    link = "https://rnm.franceagrimer.fr/prix?LIBCOD={}".format(libcod)
    req = requests.post(link)
    html = req.content
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"class": "tabcot"})
    tbody = table.find("tbody")
    for tr in tbody.findAll("tr"):
        date_inf = []
        for td in tr.findAll("td"):
            date_inf.append(td.text.replace('\xa0', '').strip())
        information.append(date_inf)
    return information

def make_dates_json():
    dates = {}
    dates['dates'] = []
    temp = []
    with open('all_details.json', 'r') as f:
        details = json.load(f)
    for product in details['data']:
        for types in product['types']:
            dates_ = types[1]
            for date in dates_:
                if date[0] not in temp:
                    temp.append(date[0])
    temp.sort(key=lambda date: datetime.strptime(date, "%d/%m/%y"), reverse=True)
    dates['dates'] = temp
    with open('dates.json', 'w') as f:
        json.dump(dates, f)

def format_data():
    with open('all_details copy.json', 'r') as f:
        details = json.load(f)
    
    ret_dets = {}
    ret_dets['data'] = []

    for product in details['data']:
        ret_product = {}
        ret_product['name'] = product['name']
        ret_product['types'] = []
        for types in product['types']:
            t = []
            t.append(types[0].strip())
            dates_ = types[1]
            d = []
            for date in dates_:
                dt = []
                dt.append(date[0].strip())
                dt.append(date[1].strip())
                dt.append(date[2].strip())
                dt.append(date[3].strip())
                d.append(dt)
            t.append(d)
            ret_product['types'].append(t)
        # print(ret_product)
        ret_dets['data'].append(ret_product)
    
    
    with open('all_details.json', 'w') as f:
        json.dump(ret_dets, f)

def get_all_details():
    details = {}
    details['data'] = []
    with open("product_links.json") as f:
        product_links = json.load(f)['links']
    for product_link in product_links:
        product = {}
        product_name = product_link.replace("https://rnm.franceagrimer.fr/prix?", "")
        product["name"] = product_name
        product["types"] = []
        types = get_product_type(product_link)
        for t in types:
            type_detail = []
            type_detail.append(t['name'])
            type_detail.append(get_type_dets(t['link']))
            product["types"].append(type_detail)
            print(".")
        pprint(product)
        details['data'].append(product)
    with open('all_details.json', 'w') as f:
        json.dump(details,f)

