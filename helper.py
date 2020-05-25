import requests
from bs4 import BeautifulSoup
import json
from pprint import pprint
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import itertools

def getSoup(link):
    req = requests.get(link)
    html = req.content
    soup = BeautifulSoup(html, "html.parser")
    return soup

def append_rows(self, values, value_input_option='RAW'):
    params = {
            'valueInputOption': value_input_option
    }
    body = {
            'majorDimension': 'ROWS',
            'values': values
    }
    return self.spreadsheet.values_append(self.title, params, body)


def get_all_products(link, file, start=0, end=9999):
    product_links = {}
    product_links["links"] = []
    soup = getSoup(link)
    products = soup.findAll("div", {"class": "listunproduit"})
    ctr = 0
    for product in products:
        link = "https://rnm.franceagrimer.fr" + product.find("a")['href']
        if ctr >= start and ctr <= end:
            product_links["links"].append(link)
        ctr = ctr + 1
    with open(file, "w") as f:
        json.dump(product_links,f)

def get_all_products_driver():
    get_all_products("https://rnm.franceagrimer.fr/prix?FRUITS", "fruits_a_n.json", 0, 41)
    get_all_products("https://rnm.franceagrimer.fr/prix?FRUITS", "fruits_o_z.json",42)
    get_all_products("https://rnm.franceagrimer.fr/prix?LEGUMES", "legumes_a_c.json",0,32)
    get_all_products("https://rnm.franceagrimer.fr/prix?LEGUMES", "legumes_d_z.json",33)
    get_all_products("https://rnm.franceagrimer.fr/prix?PECHE-ET-AQUACULTURE", "peche_aquaculture.json")
    get_all_products("https://rnm.franceagrimer.fr/prix?VIANDE", "viande.json")
    get_all_products("https://rnm.franceagrimer.fr/prix?BEURRE-OEUF-FROMAGE", "beurre.json")

def get_product_type(link):
    soup = getSoup(link)
    soup = soup.find("table", {"class": "tabcot"})
    soup = soup.find("tbody")
    rows = soup.findAll("tr")
    dets = []
    stade = ''
    marche = ''
    unite = ''
    for row in rows:
        onclick = row.find("td", {"class": "tdcotl"})
        if not onclick == None:
            det = {}
            d = onclick.find("a")
            link = d['onclick'][10:-4]
            name = d.text
            det['name'] = name.strip()
            det['stade'] = stade
            det['marche'] = marche
            det['unite'] = unite
            det['link'] = link
            dets.append(det)
        else:
            try:
                stade = row.text
                stade = re.search(r'\(cours (.*?)\)', stade).group(1)
                marche = row.find("strong").text
                unite = row.text
                unite = re.search(r'unité :(.*?)\*', unite).group(1)
            except:
                pass
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

def get_single_details(inp_file, out_file):
    details = {}
    details['data'] = []
    with open(inp_file) as f:
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
            type_detail.append(t['stade'])
            type_detail.append(t['marche'])
            type_detail.append(t['unite'])
            type_detail.append(get_type_dets(t['link']))
            product["types"].append(type_detail)
            print(".")
        details['data'].append(product)
    with open(out_file, 'w') as f:
        json.dump(details,f)

def get_all_details():
    get_single_details("fruits_a_n.json", "fruits_a_n_details.json")
    get_single_details("fruits_o_z.json", "fruits_o_z_details.json")
    get_single_details("legumes_a_c.json", "legumes_a_c_details.json")
    get_single_details("legumes_d_z.json", "legumes_d_z_details.json")
    get_single_details("peche_aquaculture.json", "peche_aquaculture_details.json")
    get_single_details("viande.json", "viande_details.json")
    get_single_details("beurre.json", "beurre_details.json")


def make_matrix(file):
    with open(file) as f:
        details = json.load(f)

    ret_dets = []

    for detail in details["data"]:
        for typee in detail["types"]:
            product = {}
            product["product"] = detail["name"]
            product["stade"] = typee[1]
            product["marche"] = typee[2]
            product["libelle"] = typee[0]
            product["unite"] = typee[3]
            for date_detail in typee[4]:
                date_format = datetime.strptime(date_detail[0], "%d/%m/%y")
                date_format = date_format.strftime("%d%B%y")
                product[date_format] = date_detail[1]
            ret_dets.append(product)
    return ret_dets

def format_matrix(matrix):
    ret_matrix = []
    heading = ['product', 'stade', 'marche', 'libelle', 'unite']
    dates = []
    for row in matrix:
        ctr = 0
        for key in row.keys():
            if key not in dates and ctr>=5:
                dates.append(key)
            ctr = ctr + 1
    dates.sort(key=lambda date: datetime.strptime(date, "%d%B%y"))
    heading.extend(dates)
    ret_matrix.append(heading)
    for row in matrix:
        ret_row = []
        for temp in heading:
            ret_row.append("")
        for key, value in row.items():
            ret_row[heading.index(key)] = value
        ret_matrix.append(ret_row)
    return ret_matrix

def gsheet_load():
    scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
    ]
    file_name = 'client_key.json'
    creds = ServiceAccountCredentials.from_json_keyfile_name(file_name,scope)
    client = gspread.authorize(creds)

    agrimer = client.open('Fruits A-N').sheet1
    new_matrix = make_matrix('fruits_a_n_details.json')
    prev_matrix = agrimer.get_all_records()
    for new_row in new_matrix:
        for prev_row in prev_matrix:
            if new_row['libelle'].lower() == prev_row['libelle'].lower():
                for key, value in new_row.items():
                    if key not in prev_row.keys():
                        prev_row[key] = value
    m = format_matrix(prev_matrix)
    agrimer.clear()
    append_rows(agrimer, m)
    print(".")

    agrimer = client.open('Fruits O-Z').sheet1
    new_matrix = make_matrix('fruits_o_z_details.json')
    prev_matrix = agrimer.get_all_records()
    for new_row in new_matrix:
        for prev_row in prev_matrix:
            if new_row['libelle'].lower() == prev_row['libelle'].lower():
                for key, value in new_row.items():
                    if key not in prev_row.keys():
                        prev_row[key] = value
    m = format_matrix(prev_matrix)
    agrimer.clear()
    append_rows(agrimer, m)
    print(".")

    agrimer = client.open('legumes A-C').sheet1
    new_matrix = make_matrix('legumes_a_c_details.json')
    prev_matrix = agrimer.get_all_records()
    for new_row in new_matrix:
        for prev_row in prev_matrix:
            if new_row['libelle'].lower() == prev_row['libelle'].lower():
                for key, value in new_row.items():
                    if key not in prev_row.keys():
                        prev_row[key] = value
    m = format_matrix(prev_matrix)
    agrimer.clear()
    append_rows(agrimer, m)
    print(".")

    agrimer = client.open('legumes D-Z').sheet1
    new_matrix = make_matrix('legumes_d_z_details.json')
    prev_matrix = agrimer.get_all_records()
    for new_row in new_matrix:
        for prev_row in prev_matrix:
            if new_row['libelle'].lower() == prev_row['libelle'].lower():
                for key, value in new_row.items():
                    if key not in prev_row.keys():
                        prev_row[key] = value
    m = format_matrix(prev_matrix)
    agrimer.clear()
    append_rows(agrimer, m)
    print(".")

    agrimer = client.open('viande').sheet1
    new_matrix = make_matrix('viande_details.json')
    prev_matrix = agrimer.get_all_records()
    for new_row in new_matrix:
        for prev_row in prev_matrix:
            if new_row['libelle'].lower() == prev_row['libelle'].lower():
                for key, value in new_row.items():
                    if key not in prev_row.keys():
                        prev_row[key] = value
    m = format_matrix(prev_matrix)
    agrimer.clear()
    append_rows(agrimer, m)
    print(".")

    agrimer = client.open('peache_aquaculture').sheet1
    new_matrix = make_matrix('peche_aquaculture_details.json')
    prev_matrix = agrimer.get_all_records()
    for new_row in new_matrix:
        for prev_row in prev_matrix:
            if new_row['libelle'].lower() == prev_row['libelle'].lower():
                for key, value in new_row.items():
                    if key not in prev_row.keys():
                        prev_row[key] = value
    m = format_matrix(prev_matrix)
    agrimer.clear()
    append_rows(agrimer, m)
    print(".")

    agrimer = client.open('beurre_oeufs_fromage').sheet1
    new_matrix = make_matrix('beurre_details.json')
    prev_matrix = agrimer.get_all_records()
    for new_row in new_matrix:
        for prev_row in prev_matrix:
            if new_row['libelle'].lower() == prev_row['libelle'].lower():
                for key, value in new_row.items():
                    if key not in prev_row.keys():
                        prev_row[key] = value
    m = format_matrix(prev_matrix)
    agrimer.clear()
    append_rows(agrimer, m)
    print(".")
