# A friend was building a drink-tracking app, and needed a database of drinks with their alcohol contents.
# He paid me $100 to build this scraper for the Dan Murphy's online database.
# This went through multiple iterations to stop it from being unbearably slow. The databse was so large a selenium-based scraper would've taken too long,
# so I had to interact with the api directly (which isn't at all protected for some reason).

import requests
import pandas as pd
import re
import os
import tqdm # for progress bars

pageSize = 100
nPages = 90
doCaching = True
cacheFile = "cached_dm_stockcodes.txt"
saveFile = 'output.csv'

sesh = requests.Session()
re_number = re.compile("\d+\.?\d*") # matches any number

# program start
def main():
    # if doing caching, attempt to retrieve stockcodes from cache file, else scrape from 'all' page
    if doCaching:
        if os.path.exists(cacheFile):
            with open(cacheFile) as f:
                codes = f.read().split(',')
                print("Codes fetched from cache")
        else:
            codes = getStockCodes()
            with open(cacheFile,'w') as f:
                f.write(','.join(codes))
    else:
        codes = getStockCodes()
    # given stock codes, get details of each. returns dict. (attempts to discard all non-alcoholic drinks and accessories)
    drinks = getDrinks(codes)
    # save details to file and end program
    saveDrinks(drinks)

# get the list of codes to be scraped. returns very long list of dicts. takes ~5 minutes
def getStockCodes():
    codes = []
    for pageNumber in bar(range(1, nPages + 1), 'Fetching Codes '):
        # send request
        response = sesh.get(f"https://api.danmurphys.com.au/apis/ui/ProductGroup/Products/all?pageSize={pageSize}&pageNumber={pageNumber}")
        # parse out codes
        codes.extend(parseCodes(response.json()))
    return codes

# given api response, extract stockcode. ignores bundles, but I don't think there are any
def parseCodes(json):
    codes = []
    for item in json['Items']:
        if(len(item['Products']) > 1):
            print("found a bundle")
            continue
        codes.append(item['Products'][0]['Stockcode'])
    return codes

# given list of stockcodes, return all drinks (modelled as dicts). Attempts to discard products that aren't alcoholic drinks.
def getDrinks(codes):
    drinks = []
    for code in bar(codes,"Fetching Drinks"):
        # make api request
        response = sesh.get(f"https://api.danmurphys.com.au/apis/ui/product/{code}")
        product = response.json()['Products'][0]
        
        try:
            drink = {'UID': code, 'Type': product['Categories'][0]['Name']}
        except IndexError:
            print(code,"has no type")
            continue

        lookup = {
            'webbrandname': 'Brand',
            'webtitle': 'Name',
            'webmaincategory': 'Type',
            'varietal': 'SubType',
            'webalcoholpercentage': 'AlcoholContent',
            'webcountryoforigin': 'Region'
        }
        # main lookup - searches for properties common to all types
        for detail in product['AdditionalDetails']:
            if detail['Name'] in lookup and lookup[detail['Name']] not in drink:
                drink[lookup[detail['Name']]] = detail['Value']

        if 'SubType' not in drink:
            drink['SubType'] = product['Categories'][-1]['Name']

        drink['Type'] = drink['Type'].title()
        drink['SubType'] = drink['SubType'].title()

        # convert AlcoholContent to float
        # if this finds two numbers, e.g. in '12.9 - 15.1%', it currently just choooses the first
        try:
            drink['AlcoholContent'] = float(re.findall(re_number, drink['AlcoholContent'])[0])
        except (KeyError, IndexError): # drink has no alcohol or Various% alcohol; skip it
            continue

        # if it's not an alchoholic drink, don't add to list
        if drink['AlcoholContent'] == 0 or drink['Type'] in ["Zero%* Alcohol Drinks", "Gifts", "Accessories", "Food Snacks"] :
            continue

        drinks.append(drink)
    return drinks

# tqdm progress bar customiser
def bar(iterable, desc):
    return tqdm.tqdm(iterable, desc, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} ({elapsed})")
        
def saveDrinks(drinks):
    df = pd.DataFrame(drinks)
    df.to_csv(saveFile,index=False)
    print("Done")

if __name__ == '__main__':
    main()