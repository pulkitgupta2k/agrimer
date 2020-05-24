import requests
from bs4 import BeautifulSoup
import json
from pprint import pprint
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

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
    # link = "https://rnm.franceagrimer.fr/prix?FRUITS-ET-LEGUMES"
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

def make_dates_json():
    dates = {}
    dates['dates'] = []
    temp = []
    temp = temp.extend(dates_separate("fruits_a_n_details.json"))
    temp = temp.extend(dates_separate("fruits_o_z_details.json"))
    temp = temp.extend(dates_separate("legumes_a_c_details.json"))
    temp = temp.extend(dates_separate("legumes_d_z_details.json"))
    temp = temp.extend(dates_separate("peche_aquacuture_details.json"))
    temp = temp.extend(dates_separate("viande_details.json"))
    temp = temp.extend(dates_separate("beurre_details.json"))
    temp.sort(key=lambda date: datetime.strptime(date, "%d/%m/%y"), reverse=True)
    dates['dates'] = temp
    with open('dates.json', 'w') as f:
        json.dump(dates, f)

def dates_separate(file):
    temp = []
    with open(file, 'r') as f:
        details = json.load(f)
    for product in details['data']:
        for types in product['types']:
            dates_ = types[1]
            for date in dates_:
                if date[0] not in temp:
                    temp.append(date[0])
    return temp

# def format_data():
#     with open('all_details copy.json', 'r') as f:
#         details = json.load(f)
    
#     ret_dets = {}
#     ret_dets['data'] = []

#     for product in details['data']:
#         ret_product = {}
#         ret_product['name'] = product['name']
#         ret_product['types'] = []
#         for types in product['types']:
#             t = []
#             t.append(types[0].strip())
#             dates_ = types[1]
#             d = []
#             for date in dates_:
#                 dt = []
#                 dt.append(date[0].strip())
#                 dt.append(date[1].strip())
#                 dt.append(date[2].strip())
#                 dt.append(date[3].strip())
#                 d.append(dt)
#             t.append(d)
#             ret_product['types'].append(t)
#         # print(ret_product)
#         ret_dets['data'].append(ret_product)
    
    
#     with open('all_details.json', 'w') as f:
#         json.dump(ret_dets, f)

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
        pprint(product)
        details['data'].append(product)
    with open(out_file, 'w') as f:
        json.dump(details,f)

def get_all_details():
    get_single_details("fruits_a_n.json", "fruits_a_n_details.json")
    get_single_details("fruits_o_z.json", "fruits_o_z_details.json")
    get_single_details("legumes_a_c.json", "legumes_a_c_details.json")
    get_single_details("legumes_d_z.json", "legumes_d_z_details.json")
    get_single_details("peche_aquacuture.json", "peche_aquacuture_details.json")
    get_single_details("viande.json", "viande_details.json")
    get_single_details("beurre.json", "beurre_details.json")


def make_matrix():
    with open("all_details.json") as f:
        details = json.load(f)
    with open("dates.json") as f:
        dates = json.load(f)

    ret_dets = []

    for product in details['data']:
        ret_product = {}
        ret_product['name'] = product['name']
        heading = []
        ret_product['rows'] = []

        for d in dates['dates']:
            heading.append(d)
        heading.insert(0, 'unite')
        heading.insert(0, 'libelle')
        heading.insert(0, 'marche')
        heading.insert(0, 'stade')
        heading.insert(0, 'product')
        ret_product['rows'].append(heading)

        for types in product['types']:
            t = []
            for d in dates['dates']:
                t.append('')
            dates_price = types[5]
            for date in dates_price:
                for index, d in enumerate(dates['dates']):
                    if date[0] == d:
                        t[index] = date[1]
                        break
            t.insert(0, types[4])
            t.insert(0, types[3])
            t.insert(0, types[2])
            t.insert(0, types[1])
            t.insert(0, types[0])
            ret_product['rows'].append(t)
        ret_dets.append(ret_product)
    

    return ret_dets

def gsheet_load():
    scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
    ]
    file_name = 'client_key.json'
    creds = ServiceAccountCredentials.from_json_keyfile_name(file_name,scope)
    client = gspread.authorize(creds)
    ctr = 1
    agrimer = client.open('agrimer_{}'.format(ctr))
    matrixs = make_matrix()
    for matrix in matrixs:
        print(matrix['name'])
        try:
            worksheet = agrimer.worksheet(matrix['name'])
        except:
            worksheet = agrimer.add_worksheet(title= matrix['name'], rows="100", cols="20")
        try:
            worksheet.clear()
            append_rows(worksheet, matrix['rows'])
        except Exception as e:
            ctr = ctr + 1
            print("________________Spreadsheet Changed__________________-")
            agrimer = client.open('agrimer_{}'.format(ctr))
            try:
                worksheet = agrimer.worksheet(matrix['name'])
            except:
                worksheet = agrimer.add_worksheet(title= matrix['name'], rows="100", cols="20")
            worksheet.clear()
            append_rows(worksheet, matrix['rows'])

# get_all_products_driver()
# get_product_type("https://rnm.franceagrimer.fr/prix?ABRICOT")
get_all_details()