import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import re
import json
import streamlit as st
import pandas as pd

URL = "https://warframe.com/droptables"  # <-- PUT YOUR REAL URL HERE

# -------------------------
# FETCH PAGE
# -------------------------
st.text("Fetching data")
st.set_page_config(page_title="Wareframe W2F Tool")


response = requests.get(URL)
soup = BeautifulSoup(response.text, "lxml")

# -------------------------
# PARSE MISSIONS
# -------------------------



def parse_missions(soup):
    data = []

    table = soup.select_one("#missionRewards + table")
    if not table:
        return data

    current_mission = None
    current_rotation = None

    for row in table.find_all("tr"):
        th = row.find("th")
        td = row.find_all("td")

        if th:
            text = th.get_text(strip=True)

            if "/" in text:
                current_mission = text
                current_rotation = None

            elif "Rotation" in text:
                current_rotation = text.replace("Rotation", "").strip()

        elif td and len(td) == 2:
            item = td[0].get_text(strip=True)
            rarity = td[1].get_text(strip=True)

            if item:
                data.append({
                    "source_type": "mission",
                    "source_name": current_mission,
                    "subtype": current_rotation,
                    "item": item,
                    "rarity": rarity
                })

    return data


# -------------------------
# PARSE RELICS
# -------------------------

def parse_relics(soup):
    data = []

    table = soup.select_one("#relicRewards + table")
    if not table:
        return data

    current_relic = None
    current_refinement = None

    for row in table.find_all("tr"):
        th = row.find("th")
        td = row.find_all("td")

        if th:
            text = th.get_text(strip=True)

            match = re.match(r"(.*)\((.*)\)", text)
            if match:
                current_relic = match.group(1).strip()
                current_refinement = match.group(2).strip()

        elif td and len(td) == 2:
            item = td[0].get_text(strip=True)
            rarity = td[1].get_text(strip=True)

            if item:
                data.append({
                    "source_type": "relic",
                    "source_name": current_relic,
                    "subtype": current_refinement,
                    "item": item,
                    "rarity": rarity
                })

    return data


# -------------------------
# RUN SCRAPERS
# -------------------------

mission_data = parse_missions(soup)
relic_data = parse_relics(soup)

all_data = mission_data + relic_data

st.text(f"Total records: {len(all_data)}")

# -------------------------
# BUILD FAST INDEX
# -------------------------

item_index = defaultdict(list)

for d in all_data:
    item_index[d["item"]].append(d)

# -------------------------
# SEARCH FUNCTIONS
# -------------------------

def search_item(item, depth=0):
    results = item_index.get(item, [])

    if not results:
        return ["Item not found"]

    output = []
    indent = "  " * depth

    for d in results:
        subtype = d["subtype"] if d["subtype"] else "Unknown"

        # -------------------------
        # CASE 1: MISSION
        # -------------------------
        if d["source_type"] == "mission":
            output.append(
                d
            )

        # -------------------------
        # CASE 2: RELIC
        # -------------------------
        elif d["source_type"] == "relic":
            relic_name = d["source_name"]

            relic_drops = item_index.get(relic_name, [])

            mission_drops = [rd for rd in relic_drops if rd["source_type"] == "mission"]
            if mission_drops:
                output.append(d)

    if not output:
        output.append("All Relics for this item has been vaulted :(")
    return output


def search_item_fuzzy(query):
    query = query.lower()
    results = []

    for item in item_index:
        if query in item.lower():
            for d in item_index[item]:
                if d["source_type"] == "mission":
                    results.append(
                        f'{item} → Mission: {d["source_name"]} | Rotation {d["subtype"]} | {d["rarity"]}'
                    )
                else:
                    results.append(
                        f'{item} → Relic: {d["source_name"]} ({d["subtype"]}) | {d["rarity"]}'
                    )

    return results or ["No matches found"]


# -------------------------
# OPTIONAL: SAVE DATA
# -------------------------

with open("warframe_data.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)


# -------------------------
# TESTS
# -------------------------

# print("\n--- EXACT SEARCH ---")
# for r in search_item("Xaku Prime Systems Blueprint"):
#     print(r)

hey = st.text("")
st.title("Warframe W2F Tool")

st.text("This my Warframe Where To Farm tool, its based on the information from the offical droptables, it might be a little slow but it works in real time")


def all_same_source_type(data):
    values = {d.get("source_type") for d in data}

    if values == {"mission"}:
        return 1
    elif values == {"relic"}:
        return 2
    else:
        return 0
    
stitem = st.text_input("Enter your item's name")
results = search_item(stitem)

if stitem:
    searchType = all_same_source_type(results)
    if searchType == 1 :
        df = pd.DataFrame(results)
        df = df.drop(columns="item")
        df = df.rename(columns={
            "source_type": "Source",
            "source_name": "Name",
            "subtype": "Rotation",

        })
        st.table(data = df)

    elif searchType == 2:
        df = pd.DataFrame(results)
        df = df.drop(columns="item")
        df = df.rename(columns={
            "source_type": "Source",
            "source_name": "Relic Name",
            "subtype": "Refinement",

        })
        st.table(data = df)

        st.text("Where to find this relic: ")
        findRelic = search_item(df.loc[0]["Relic Name"])
        
        newDf = pd.DataFrame(findRelic)
        newDf = newDf.drop(columns="item")
        newDf = newDf.rename(columns={
            "source_type": "Source",
            "source_name": "Name",
            "subtype": "Rotation",

        })
        st.table(data = newDf)


    elif searchType == 0:
        st.table(data = pd.DataFrame(results))



