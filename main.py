# %%
import glob
import json
import logging
import os
import re

import pandas as pd

import requests

# %%
logging.basicconfig(
    filename="data_analysis.log",
    level=logging.info,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

##########################################################
################# DSP Csv stuff ##################
##########################################################
# %%

df_dsp_tra_map = pd.read_csv("dsp_tra_map.csv")
df_dsp_tra_map.head()
# %%
######## DATA CLEANUP ###############
df_dsp_tra_map["ApplicationName"] = df_dsp_tra_map["ApplicationName"].str.upper()
df_dsp_tra_map.head()

# %%


# Returns empty if not found
# names is a list because there can be multiple applications per tro
def get_dsp_names_from_application_name(names: list):
    # Ensure we are working with a list; if it's a single string, wrap it
    if isinstance(names, str):
        names = [names]

    # we can have more than one dsp submit for the council as one dsp can do a TTRO and another PTRO - ask ben about this
    possible_dsps = set()

    for i in DSP_NAMES:
        if any(i in str(name) for name in names):
            possible_dsps.add(i)

    if len(possible_dsps) == 1:
        return possible_dsps.pop()
    elif len(possible_dsps) == 0:
        return None
    return possible_dsps


def test_get_dsp_name_from_application_name():
    print(get_dsp_names_from_application_name(df_dsp_tra_map["ApplicationName"][8]))


test_get_dsp_name_from_application_name()

######### Quality of Life checks #################
# %%

application_name = df_dsp_tra_map["ApplicationName"]
total_applications = len(application_name)
no_1 = 0
no_2 = 0
no_3 = 0
no_4 = 0
no_5 = 0
no_6 = 0
no_7 = 0
no_other = 0
council_name_set = set()
dsp_name_set = set()
publisher_name_set = set()  # should only have 'Publisher'
application_name_set = set()  # should only have 'Application'

for i in application_name:
    split = i.split("-")
    if len(split) == 1:
        # print of split below
        # ['Ben Pauley']
        # ['Ben Pauley']
        # ['Ben Pauley']
        # ['Ben Pauley Public Beta Publisher App']
        # ['HCC']
        # ['WSCC 2']
        # ['CroydonDTRO']
        # ['DerbyDTRO']
        no_1 += 1

    elif len(split) == 2:
        # print of split
        # ['OneViewPlus', 'CheshireWestAndChester']
        no_2 += 1
    elif len(split) == 3:
        # ['TFL', 'Publisher', 'Application']
        # ['CENTRALBEDFORDSHIRECOUNCIL_SYMOLOGY', 'PUBLISHER', 'Application']
        no_3 += 1
    elif len(split) == 4:
        dsp_name_set.add(split[1])
        no_4 += 1
    elif len(split) == 5:
        dsp_name_set.add(split[1])
        no_5 += 1
    elif len(split) == 6:
        dsp_name_set.add(split[2])
        no_6 += 1
    elif len(split) == 7:
        dsp_name_set.add(split[3])
        no_7 += 1
    else:
        no_other += 1
print(
    f"No 7: {no_7}, No 6: {no_6}, No 5: {no_5}, No 4: {no_4}, No 3: {no_3}, No 2: {no_2}, No 1: {no_1}, No Other: {no_other}\nTotal counted: {no_7 + no_6 + no_5 + no_4 + no_3 + no_2 + no_1 + no_other}, Total All: {total_applications}"
)
# %%
print(dsp_name_set)

# {'YourOrganisation', 'Integration', 'BuchananComputing', 'StatMap', 'Causeway', 'Appyway', 'PA', 'SYMOLOGY', 'CAUSEWAY', 'Buchanancomputing'}

DSP_NAMES = {
    # "YOURORGANISATION",
    "BUCHANANCOMPUTING",
    # "INTEGRATION",
    # "PA",
    "CAUSEWAY",
    "SYMOLOGY",
    "APPYWAY",
    "STATMAP",
}

# %%
# check if all unique ids and their appId length add up to the original length of the df_dsp_tra_map
df_dsp_tra_map_unique_by_id = (
    df_dsp_tra_map.groupby("TRAId").agg(lambda x: list(x.unique())).reset_index()
)

# %%
print(len(df_dsp_tra_map))  # 209

total = 0
for i in df_dsp_tra_map_unique_by_id["AppId"]:
    total += len(i)
print(total)  # total = 209 therefore all AppId's match to a valid existing TRAId
# %%
df_dsp_tra_map_unique_by_id.head()
# %%
dsps = []
for i in df_dsp_tra_map_unique_by_id["ApplicationName"]:
    dsps.append(get_dsp_names_from_application_name(i))

df_dsp_tra_map_unique_by_id["DspNames"] = dsps

# %%
df_dsp = df_dsp_tra_map_unique_by_id
df_dsp.head(30)

# %%
df_dsp[df_dsp["TRAId"] == 840]["ApplicationName"].values

# %%
df_dsp["DspNames"].value_counts()

# %%
##########################################################
################# TRO - JSON DATA STUFF ##################
##########################################################

# %%
# create a dataframe of the data
DATA_FOLDER_PATH = "data-mod/*.json"

all_data = []

for file_path in glob.glob(DATA_FOLDER_PATH):
    with open(file_path, "r") as f:
        data = json.load(f)
        all_data.append(data)

# record_path: the path to the list of items we want as rows
# meta: top-level fields we want to keep in every row
# todo - this needs work. from what i see you need to declare which top level rows you want as meta as things can get very nested. may need adjusting in the future for other fields
df_data = pd.json_normalize(
    all_data,
    record_path=["source", "provision"],
    meta=[
        ["source", "tro_name"],
        ["source", "reference"],
        ["source", "tra_creator"],
        ["source", "tra_affected"],
        ["source", "current_tra_owner"],
        ["source", "made_date"],
    ],
    errors="ignore",
)
df_data.head()
# df_data['source.tra_creator']

# %%

DATA_FOLDER_PATH = "data-mod/*.json"
tra_creators = []
for file_path in glob.glob(DATA_FOLDER_PATH):
    data: dict
    with open(file_path, "r") as f:
        data = json.load(f)
    tra_creators.append(data["source"]["tra_creator"])

row = df_dsp[df_dsp["TRAId"] == tra_creators[20]].iloc[0]
print(row)
# %%
### Modify df_data to add the dsp name


# %%

# Get the traId then see which records have that
traId = df_dsp_tra_map["TRAId"]
traId


# %%
def does_tro_name_have_a_valid_year(text):
    years = re.findall(r"\b(19[5-9]\d|20[0-4]\d|2050)\b", text)
    if len(years) > 0:
        return True
    else:
        return False


def test():
    print(does_tro_name_have_a_valid_year(" 2020 fd License (Other) on 2020 Abbey Street"))
    print(does_tro_name_have_a_valid_year("License (Other) on 2020 Abbey Street"))
    print(does_tro_name_have_a_valid_year("THE COUNTY OF SOMERSETÂ  PROHIBITION AND RESTRICTION OF STOPPING, WAITING, LOADING AND UNLOADING AND ON-STREET PARKING TAUNTON DEANE ORDER 2012 (AMENDMENT NO.11) ORDER 2016"))
    print(does_tro_name_have_a_valid_year("License (Other) on 3000 Abbey Street"))
    print(does_tro_name_have_a_valid_year("License (Other) on  2050 Abbey Street"))


test()
# %%


# %%
API_KEY = "94DyTsgHAMR7tXFp56hW8kHPmXAUfvLK"
# resp = requests.get(f"https://api.os.uk/positioning/osnet/v1?key={API_KEY}")
# print(resp.json)


def check_road_exists(road_name):
    """
    Checks if a road name exists in Great Britain using the OS Names API.
    """
    url = "https://api.os.uk/search/names/v1/find"

    # Parameters for the search
    params = {
        "query": road_name,
        "key": API_KEY,
        "maxresults": 1,
        "format": "JSON",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Check for HTTP errors

        data = response.json()
        with open("response.json", "w") as file:
            file.write(str(data))
        print(response.status_code)
        # # Check if any features were found in the response
        # if "features" in data and len(data["features"]) > 0:
        #     print(f"✅ Road name '{road_name}' exists in the database.")

        #     # Print the first few matches for verification
        #     for feature in data["features"]:
        #         properties = feature["properties"]
        #         # Filter specifically for road-related types
        #         if properties.get("LOCAL_TYPE") in ["Named_Road", "Numbered_Road"]:
        #             print(
        #                 f" - Match found: {properties.get('NAME1')} in {properties.get('DISTRICT_BOROUGH')}"
        #             )
        #     return True
        # else:
        #     print(f"❌ No matches found for '{road_name}'.")
        #     return False

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


check_road_exists("No Way this road exists")


# %%
def data_checks(json_file_path) -> bool:
    """Check if the 'tro_name' contains the road name and has a valid number."""
    data: dict
    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        logging.error(f"File '{json_file_path}' not found.")
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from the file '{json_file_path}'.")

    # todo check data exists or something
    ############ TRA NAME ##############
    tro_name = data["source"]["tro_name"]
    road_name = data["source"]["provision"][0]["regulated_place"][0]["description"]
    # instead of logging the data we should put to a csv or something and then open with pandas to understand better
    if road_name not in tro_name:
        logging.info(f"The road name '{road_name}' is NOT found in 'tro_name'.")
        return False
    else:
        logging.info(f"The road name '{road_name}' is found in 'tro_name'.")

    does_tra_name_have_a_year = does_tro_name_have_a_valid_year(tro_name)
    if does_tra_name_have_a_year is False:
        logging.info(f"'tro_name' '{tro_name}' does NOT contain a valid number.")
        return False
    else:
        logging.info(f"'tro_name' '{tro_name}' does contain a valid number.")

    return True


# %%
directory_path = "data-mod/"
for filename in os.listdir(directory_path):
    if filename.endswith(".json"):
        data_checks(os.path.join(directory_path, filename))

############## Querying the OS API to check if the road name exists
