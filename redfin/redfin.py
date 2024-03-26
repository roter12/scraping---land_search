import os
import re
import sys
import time
import json
import datetime
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver


# Contants
# https://www.redfin.com/zipcode/49068/filter/property-type=land,min-lot-size=1-acre,max-lot-size=20-acre,hoa=0,include=sold-2yr
# https://www.redfin.com/county/1360/MI/Calhoun-County/filter/property-type=land,min-lot-size=1-acre,hoa=0,include=sold-2yr

url_base = "https://www.redfin.com"
url_county = "/county/{}/{}/{}-County"
url_zipcode = "/zipcode/{}"
url_filter = "/filter/property-type=land,min-lot-size={}-acre,max-lot-size={}-acre,hoa=0,include=sold-2yr"


# Save as a file
def save_file(text, filename = 'output/test.tmp'):
	if type(text) != 'str':
		text = str(text)
	file = open(filename, "w", encoding="utf-8")
	file.write(text)
	file.close()


# Read file
def read_file(filename = 'output/test.tmp'):
    file = open(filename, "r", encoding="utf-8")
    text = file.read()
    file.close()
    return text


# Save as json file
def save_json_file(json_value, file_path):
    with open(file_path, "a") as file:
        # Write the JSON data to the file
        json.dump(json_value, file)


# Get html content
driver = None
def get_html_with_request(url):
	global driver
	if not driver:
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
def parse_one_page(html, page_idx):
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


# Parse argument
if len(sys.argv) == 2 and sys.argv[1] == "-h":
    print(f"Usage:")
    print(f"\tpython {os.path.basename(sys.argv[0])} <zip code> <min acres> <max acres>")
    print(f"\tpython {os.path.basename(sys.argv[0])} <county> <state> <redfin code> <min acres> <max acres>")
    sys.exit(1)
    
if len(sys.argv) != 4 and len(sys.argv) != 6:
    input_first = input("County or Zipcode:")
    if 0 == len(re.findall(r'^\d+$', input_first)):
        input_state = input("State:")
        input_code = input("Redfin code:")

        input_min = input("Min size acre:")
        input_max = input("Max size acre:")
        url_main = url_base + url_county.format(input_code, input_state, input_first) + url_filter.format(input_min, input_max)
    else:
        input_min = input("Min size acre:")
        input_max = input("Max size acre:")
        url_main = url_base + url_zipcode.format(input_first) + url_filter.format(input_min, input_max)
else:
    if len(sys.argv) == 4:
        url_main = url_base + url_zipcode.format(sys.argv[1]) + url_filter.format(sys.argv[2], sys.argv[3])
    else:
        url_main = url_base + url_county.format(sys.argv[3], sys.argv[2], sys.argv[1]) + url_filter.format(sys.argv[4], sys.argv[5])

# Start scraping
i = 0

data = {"Website":[], "Zipcode":[], "Lot size":[], "Price":[]}
while True:
    i += 1
    if i > 1:
        url_page = url_main + f"/page-{i}"
    else:
        url_page = url_main
    print(f"Page {i}: {url_page}\n")

    html = get_html_with_request(url_page)
    #save_file(html)
    #html = read_file()
    if html == "":
        break

    results, last_page = parse_one_page(html, i)
    for j in range(len(results['zipcode'])):
        data['Website'].append('Redfin')
    data['Zipcode'].extend(results['zipcode'])
    data['Lot size'].extend(results['lot'])
    data['Price'].extend(results['price'])
    if last_page == True:
        break
    

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


# Save DataFrame to a CSV file
path = output_dir + os.sep + f"land-data(Redfin).csv"
df = pd.DataFrame(data)
df.to_csv(path, index=False)
print("\nFinished!")
print("Output file:", path)