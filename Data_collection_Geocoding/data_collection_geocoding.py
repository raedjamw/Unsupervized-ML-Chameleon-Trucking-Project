# -*- coding: utf-8 -*-
"""Data_collection_Geocoding.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1gJjLvhik2GO838-lLwQfXqqrvOhUZCjc
"""

import requests
import re
import mysql.connector
from sqlalchemy import create_engine
import logging
import pandas as pd
import time
import json

# import sys
# sys.path.append(r'C:\Users\Rae-Djamaal\Anaconda3\Lib\Git_Uploads\chameleon_project_phase1_Final\Phase_1')

# User Defined Function
from nneigh.nneigh import nearest_neighbor
# User Defined Function
from SQL_Mods.sql_mods import MySQL_Operations

"""Connect to Sql server and get the IS_Coords_to_Geocode table"""

# Call the instance MySQL Class
db_call_1 = MySQL_Operations('insert_your_user','password','host','insert_your_database')

# check the engine
print(db_call_1.Engine_Connection()[0])

# check the connection
print(db_call_1.Database_Connection()[0])

# get the connection object
connection = db_call_1.Database_Connection()[1]

# Create the cursor
cursor = connection.cursor(prepared=True)

# load the sql table and convert table to dataframe
IS_Coords_to_Geocode = pd.read_sql('SELECT * FROM IS_Coords_to_Geocode', con=engine)

# Rename columns
IS_Coords_to_Geocode.rename(columns={'USDOT': "usdot", 'FULL_ADDRESS': "address"}, inplace=True)

here_api_key = "insert_your_api key"

# Run the HERE Maps Geocoding API
start = time.time()
dict_list = []
dot_fails = []
# initialize the rejected requests
rejects = 0
# iterate over the rows of the df
for i, r in IS_Coords_to_Geocode.iterrows():
    # clean address format by removing hastags
    search_text = f"{r['FULL_ADDRESS'].replace('#','')}"
    # intialize the url object with full address inserted and api key insert
    url = f"https://geocoder.ls.hereapi.com/6.2/geocode.json?searchtext={search_text.replace('&','').replace(' ','%20')}"+f'&&apiKey={here_api_key}'
    # perform the get request
    response = requests.get(url)
    # access the response body
    j = response.content
    try:
        USDOT = r['USDOT']
        # check that an address exist
        if len(json.loads(j)['Response']['View']) > 0:
            # get the lat and lon coordinates of this addres
            lat = json.loads(j)['Response']['View'][0]['Result'][0]['Location']['DisplayPosition']['Latitude']
            lon = json.loads(j)['Response']['View'][0]['Result'][0]['Location']['DisplayPosition']['Longitude']
            # append them to the list
            dict_list.append({'USDOT':f'{USDOT}','lat':lat,'lon':lon})
        else:
          # address not found condition
            search_text = f"{r['FULL_ADDRESS'].replace('#','')}"
            url = f"https://geocoder.ls.hereapi.com/6.2/geocode.json?searchtext={search_text.replace(' ','%20')}&&apiKey={here_api_key}"
            response = requests.get(url)
            j = response.content
            # inscrease rejects
            rejects = rejects+1
            dot_fails.append({'row':r,'json':json.loads(j),'ex':'NA'}) 
    # check for another fail request(e.g. exceeded limit)        
    except Exception as ex:
        dot_fails.append({'row':r,'json':json.loads(j),'ex':ex})
        # increase no of rejects
        rejects = rejects+1
print(f"# of rejected requests: {rejects}")
print(f"# of coordinates acquired: {len(dict_list)}")
end = time.time()
print(f"Total Run Time: {(end-start)/60} minutes")
# save coordinates to dataframe
coord_df = pd.DataFrame(dict_list)

# rename columns
coord_df.rename(columns={'lat': "LAT",'lon':'LON'}, inplace=True)

# Get the orginal cords we have
= pd.read_sql('SELECT * FROM is_company_coordinates', con=engine)

# concat just geocoded cords to cords we had previously
frames = [IS_Coords,coord_df]
Coords_to_Find = pd.concat(frames)

# Save the Coords_to_Find to MySQL Server
Coords_Found.to_sql('is_company_coordinates', engine, if_exists='replace', index=False)