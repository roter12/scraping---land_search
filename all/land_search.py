import os
import re
import sys
import time
import json
import datetime
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

# Scraping variables
url_base1 = "https://www.redfin.com"
url_county1 = "/county/{}/{}/{}-County"
url_zipcode1 = "/zipcode/{}"
url_filter1 = "/filter/property-type=land,min-lot-size={}-acre,max-lot-size={}-acre,hoa=0,include=sold-2yr"

KEYWORD_START_MAIN2 = '<script id="__NEXT_DATA__" type="application/json">'
KEYWORD_END_MAIN2 = '</script>'

url_base2 = "https://www.realtor.com/realestateandhomes-search"
url_county2 = "/{}-County_{}"
url_zipcode2 = "/{}"
url_filter2 = "/type-land/show-recently-sold/lot-sqft-{}-{}/hoa-no,known"

KEYWORD_START_MAIN3 = '<script>window.serverState = "'
KEYWORD_END_MAIN3 = '";</script>'

url_base3 = "https://www.landwatch.com"
url_county3 = "/{}-land-for-sale/{}-county"
url_zipcode3 = "/zip-{}"
url_filter3 = "/undeveloped-land/acres-{}-{}/under-contract/sold"

output_dir = ""


def get_sub_part(str, keyword_start, keyword_end):
    idx_start = str.find(keyword_start)
    if idx_start == -1:
        return ""
    idx_start += len(keyword_start)
    
    idx_end = str.find(keyword_end, idx_start)
    if idx_end == -1:
        return ""
    
    return str[idx_start:idx_end]

# 1 #######################################################################
# Get html content
driver1 = None
def get_html_with_request1(url):
	global driver1
	if not driver1:
		options = webdriver.ChromeOptions()
		options.add_argument('--ignore-certificate-errors')
		options.add_argument('--ignore-certificate-errors-spki-list')
		options.add_argument('--ignore-ssl-errors')
		options.add_argument('log-level=3')
		options.add_argument("disable-quic")
		driver1 = webdriver.Chrome(options=options)
	# time.sleep(3)
	driver1.get(url)
	return driver1.page_source

# Parsing one page
def parse_one_page1(html, page_idx):
    ret = {"zipcode":[], "lot":[], "price":[]}
    b_lastpage = False

    # Check if the last page.
    soup = BeautifulSoup(html, "html.parser")
    a_tags = soup.findAll('a', attrs={'class':'goToPage'})
    if a_tags == None:
        b_lastpage = True
    else:
        if len(a_tags) == 0:
            b_lastpage = True
        else:
            if a_tags[-1].get_text() == str(page_idx):
                b_lastpage = True

    for div in soup.findAll('div', attrs={'class':'HomeCardContainer'}):
        address = "-"
        zipcode = "-"
        lotsize = "-"
        price = "-"

        bottomV2 = div.find('div', attrs={'class':'bottomV2'})
        if bottomV2 == None:
            continue

        anchor = bottomV2.find('div', attrs={'class':'link-and-anchor'})
        if anchor != None:
            address = anchor.get_text()
            if address == "":
                address = "-"

            zip = re.search(r'\d*$', address)
            zipcode = address[zip.start():]
            if zipcode == "":
                zipcode = "-"

        HomeStatsV2 = bottomV2.find('div', attrs={'class':'HomeStatsV2 font-size-small'})
        if HomeStatsV2 != None:
            stats = HomeStatsV2.findAll('div', attrs={'class':'stats'})
            if stats != None and len(stats) > 0:
                lotsize = re.sub(r'[^0-9\.]*', '', stats[-1].get_text())
                if lotsize == "":
                    lotsize = "-"

        el = bottomV2.find('span', attrs={'class':'homecardV2Price'})
        if el != None:
            price = re.sub(r'[^0-9\.]*', '', el.get_text())
            if price == "":
                price = "-"
        
        print(f"- Address: {address} Zipcode: {zipcode} Lot size: {lotsize} Price: {price}")
        ret['zipcode'].append(zipcode)
        ret['lot'].append(lotsize)
        ret['price'].append(price)
            
    return ret, b_lastpage

def scraping1(url):
    global output_dir
    i = 0

    data = {"Website":[], "Zipcode":[], "Lot size":[], "Price":[]}
    while True:
        i += 1
        if i > 1:
            url_page = url + f"/page-{i}"
        else:
            url_page = url
        print(f"Page {i}: {url_page}\n")

        html = get_html_with_request1(url_page)
        if html == "":
            break

        results, last_page = parse_one_page1(html, i)
        for j in range(len(results['zipcode'])):
            data['Website'].append('Redfin')
        data['Zipcode'].extend(results['zipcode'])
        data['Lot size'].extend(results['lot'])
        data['Price'].extend(results['price'])
        if last_page == True:
            break

    # Save DataFrame to a CSV file
    df = pd.DataFrame(data)
    df.to_csv(output_dir + os.sep + f"land-data(Redfin).csv", index=False)
    return data
# 2 #######################################################################
# Get html content
def get_html_with_request2(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-certificate-errors-spki-list')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('log-level=3')
    options.add_argument("disable-quic")
    driver = webdriver.Chrome(options=options)
    # time.sleep(3)
    driver.get(url)
    return driver.page_source

# Parsing one page
def parse_one_page2(html, page_idx):
    ret = {"zipcode":[], "lot":[], "price":[]}
    b_lastpage = False

    # Check if the last page.
    soup = BeautifulSoup(html, "html.parser")
    a_tags = soup.findAll('a', attrs={'class':'pagination-item'})
    if a_tags == None:
        b_lastpage = True
    else:
        if len(a_tags) == 0:
            b_lastpage = True
        else:
            if a_tags[-1].get_text() == str(page_idx):
                b_lastpage = True

    str_main = get_sub_part(html, KEYWORD_START_MAIN2, KEYWORD_END_MAIN2)
    if str_main != "":    
        obj_main = json.loads(str_main)

        try:
            for item in obj_main['props']['pageProps']['expandedProperties']:
                print(f"- Address: {item['location']['address']['line']} Zipcode: {item['location']['address']['postal_code']} Lot size: {item['description']['lot_sqft']/43560} Price: {item['description']['sold_price']}")
                ret['zipcode'].append(item['location']['address']['postal_code'])
                ret['lot'].append(item['description']['lot_sqft']/43560)
                ret['price'].append(item['description']['sold_price'])
                    
        except:
            print("Somethings wrong!")
            
    return ret, b_lastpage

def scraping2(url):
    global output_dir
    # Start scraping
    i = 0

    data = {"Website":[], "Zipcode":[], "Lot size":[], "Price":[]}
    while True:
        i += 1
        if i > 1:
            url_page = url + f"/pg-{i}"
        else:
            url_page = url
        print(f"Page {i}: {url_page}\n")

        html = get_html_with_request2(url_page)
        if html == "":
            break

        results, last_page = parse_one_page2(html, i)
        for j in range(len(results['zipcode'])):
            data['Website'].append('Realtor')
        data['Zipcode'].extend(results['zipcode'])
        data['Lot size'].extend(results['lot'])
        data['Price'].extend(results['price'])
        if last_page == True:
            break

    # Save DataFrame to a CSV file
    path = output_dir + os.sep + f"land-data(Realtor).csv"
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    return data
# 3 #######################################################################
# Get html content
driver3 = None
def get_html_with_request3(url):
	global driver3
	if not driver3:
		options = webdriver.ChromeOptions()
		options.add_argument('--ignore-certificate-errors')
		options.add_argument('--ignore-certificate-errors-spki-list')
		options.add_argument('--ignore-ssl-errors')
		options.add_argument('log-level=3')
		options.add_argument("disable-quic")
		driver3 = webdriver.Chrome(options=options)
	time.sleep(1)
	driver3.get(url)
	return driver3.page_source

# Parsing one page
def parse_one_page3(html, page_idx):
    ret = {"zipcode":[], "lot":[], "price":[]}
    b_lastpage = True

    str_main = get_sub_part(html, KEYWORD_START_MAIN3, KEYWORD_END_MAIN3)
    if str_main != "": 
        obj_main = json.loads(str_main.replace('\\\\\\\\', "").replace('\\\\\\"', "'").replace('\\"', '"'))

        try:
            for item in obj_main['searchPage']['searchResults']['propertyResults']:
                print(f"- Address: {item['address']} Zipcode: {item['zip']} Lot size: {item['acres']} Price: {item['price']}")
                ret['zipcode'].append(item['zip'])
                ret['lot'].append(item['acres'])
                ret['price'].append(item['price'])

            if obj_main['searchPage']['searchResults']['paginationData']['linkData'][-1]['description'] != str(page_idx):
                b_lastpage = False
        except:
            print("Somethings wrong!")

    return ret, b_lastpage

def scraping3(url):
    global output_dir
    # Start scraping
    i = 0

    data = {"Website":[], "Zipcode":[], "Lot size":[], "Price":[]}
    while True:
        i += 1
        if i > 1:
            url_page = url + f"/page-{i}"
        else:
            url_page = url
        print(f"Page {i}: {url_page}\n")

        html = get_html_with_request3(url_page)
        if html == "":
            break

        results, last_page = parse_one_page3(html, i)
        for j in range(len(results['zipcode'])):
            data['Website'].append('LandWatch')
        data['Zipcode'].extend(results['zipcode'])
        data['Lot size'].extend(results['lot'])
        data['Price'].extend(results['price'])
        if last_page == True:
            break

    # Save DataFrame to a CSV file
    path = output_dir + os.sep + f"land-data(LandWatch).csv"
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    return data

# Main entry
input_first = input("County or Zipcode:")
if 0 == len(re.findall(r'^\d+$', input_first)):
    input_state_long = input("State(long word - Michigan):")
    input_state = input("State(short word - MI):")
    input_code = input("Redfin code:")

    input_min = input("Min size acre:")
    input_max = input("Max size acre:")
    url_main1 = url_base1 + url_county1.format(input_code, input_state, input_first) + url_filter1.format(input_min, input_max)
    url_main2 = url_base2 + url_county2.format(input_first, input_state) + url_filter2.format(43560*int(input_min), 43560*int(input_max))
    url_main3 = url_base3 + url_county3.format(input_state_long, input_first).lower() + url_filter3.format(input_min, input_max)
else:
    input_min = input("Min size acre:")
    input_max = input("Max size acre:")
    url_main1 = url_base1 + url_zipcode1.format(input_first) + url_filter1.format(input_min, input_max)
    url_main2 = url_base2 + url_zipcode2.format(input_first) + url_filter2.format(43560*int(input_min), 43560*int(input_max))
    url_main3 = url_base3 + url_zipcode3.format(input_first) + url_filter3.format(input_min, input_max)


# create the output directory
output_dir = os.path.join('.',  'output')
if not os.path.isdir(output_dir):
    os.mkdir(output_dir)

timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

try:
    output_dir = os.path.join(output_dir, timestamp)
    os.mkdir(output_dir)
except Exception as e:
    print('Error: ' + str(e))
    print('Failed to create output directory. Aborted.')
    sys.exit(1)

# Create a new thread
all_data = {"Website":[], "Zipcode":[], "Lot size":[], "Price":[]}
data1= scraping1(url_main1)
all_data['Website'].extend(data1['Website'])
all_data['Zipcode'].extend(data1['Zipcode'])
all_data['Lot size'].extend(data1['Lot size'])
all_data['Price'].extend(data1['Price'])

data2= scraping2(url_main2)
all_data['Website'].extend(data2['Website'])
all_data['Zipcode'].extend(data2['Zipcode'])
all_data['Lot size'].extend(data2['Lot size'])
all_data['Price'].extend(data2['Price'])

data3= scraping3(url_main3)
all_data['Website'].extend(data3['Website'])
all_data['Zipcode'].extend(data3['Zipcode'])
all_data['Lot size'].extend(data3['Lot size'])
all_data['Price'].extend(data3['Price'])

path = output_dir + os.sep + f"land-data.csv"
df = pd.DataFrame(all_data)
df.to_csv(path, index=False)

print("\nFinished!")
print("Output file:", path)
print("Total count:", len(df))