import requests
from bs4 import BeautifulSoup
import json
from pprint import pprint

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
    links = []
    names = []
    for row in rows:
        onclick = row.find("td", {"class": "tdcotl"})
        if not onclick == None:
            det = onclick.find("a")
            link = det['onclick']
            name = det.text
            names.append(name)
            links.append(link)
    pprint(names)

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
            date_inf.append(td.text.replace('\xa0', ''))
        information.append(date_inf)
    pprint(information)

def driver:
    

# get_product_type("https://rnm.franceagrimer.fr/prix?ABRICOT")