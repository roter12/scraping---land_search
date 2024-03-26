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
# https://www.realtor.com/realestateandhomes-search/Calhoun-County_MI/type-land/show-recently-sold/lot-sqft-43560-4356000/hoa-no,known
# https://www.realtor.com/realestateandhomes-search/49068/type-land/show-recently-sold/lot-sqft-43560-4356000/hoa-no,known/pg-2

url_base = "https://www.realtor.com/realestateandhomes-search"
url_county = "/{}-County_{}"
url_zipcode = "/{}"
url_filter = "/type-land/show-recently-sold/lot-sqft-{}-{}/hoa-no,known"

KEYWORD_START_MAIN = '<script id="__NEXT_DATA__" type="application/json">'
KEYWORD_END_MAIN = '</script>'


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
def get_html_with_request(url):
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


def get_sub_part(str, keyword_start, keyword_end):
    idx_start = str.find(keyword_start)
    if idx_start == -1:
        return ""
    idx_start += len(keyword_start)
    
    idx_end = str.find(keyword_end, idx_start)
    if idx_end == -1:
        return ""
    
    return str[idx_start:idx_end]

# Parsing one page
def parse_one_page(html, page_idx):
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

    str_main = get_sub_part(html, KEYWORD_START_MAIN, KEYWORD_END_MAIN)
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


# Parse argument
if len(sys.argv) == 2 and sys.argv[1] == "-h":
    print(f"Usage:")
    print(f"\tpython {os.path.basename(sys.argv[0])} <zip code> <min acres> <max acres>")
    print(f"\tpython {os.path.basename(sys.argv[0])} <county> <state> <state code> <min acres> <max acres>")
    sys.exit(1)
    
if len(sys.argv) != 4 and len(sys.argv) != 6:
    input_first = input("County or Zipcode:")
    if 0 == len(re.findall(r'^\d+$', input_first)):
        input_state = input("State:")
        input_code = input("State code:")

        input_min = input("Min size acre:")
        input_max = input("Max size acre:")
        url_main = url_base + url_county.format(input_first, input_state) + url_filter.format(43560*int(input_min), 43560*int(input_max))
    else:
        input_min = input("Min size acre:")
        input_max = input("Max size acre:")
        url_main = url_base + url_zipcode.format(input_first) + url_filter.format(43560*int(input_min), 43560*int(input_max))
else:
    if len(sys.argv) == 4:
        url_main = url_base + url_zipcode.format(sys.argv[1]) + url_filter.format(43560*int(sys.argv[2]), 43560*int(sys.argv[3]))
    else:
        url_main = url_base + url_county.format(sys.argv[1], sys.argv[2]) + url_filter.format(43560*int(sys.argv[4]), 43560*int(sys.argv[5]))

# Start scraping
i = 0

data = {"Website":[], "Zipcode":[], "Lot size":[], "Price":[]}
while True:
    i += 1
    if i > 1:
        url_page = url_main + f"/pg-{i}"
    else:
        url_page = url_main
    print(f"Page {i}: {url_page}\n")

    html = get_html_with_request(url_page)
    save_file(html, 'test.tmp')
    #html = read_file('test.tmp')
    if html == "":
        break

    results, last_page = parse_one_page(html, i)
    for j in range(len(results['zipcode'])):
        data['Website'].append('Realtor')
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
path = output_dir + os.sep + f"land-data(Realtor).csv"
df = pd.DataFrame(data)
df.to_csv(path, index=False)
print("\nFinished!")
print("Output file:", path)