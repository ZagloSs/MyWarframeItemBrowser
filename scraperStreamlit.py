import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import re
import json
import streamlit as st

URL = "https://warframe-web-assets.nyc3.cdn.digitaloceanspaces.com/uploads/cms/hnfvc0o3jnfvc873njb03enrf56.html"  # <-- PUT YOUR REAL URL HERE

# -------------------------
# FETCH PAGE
# -------------------------
st.text("Fetching data")
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
                f'{indent}{item} → Mission: {d["source_name"]} | Rotation {subtype} | {d["rarity"]}'
            )

        # -------------------------
        # CASE 2: RELIC
        # -------------------------
        elif d["source_type"] == "relic":
            relic_name = d["source_name"]

            output.append(
                f'{indent}{item} → Relic: {relic_name} ({subtype}) | {d["rarity"]}'
            )

            # 🔍 Find where the relic drops
            relic_drops = item_index.get(relic_name, [])

            # 🚫 IMPORTANT: only show relic if it has mission sources
            mission_drops = [rd for rd in relic_drops if rd["source_type"] == "mission"]

            if not mission_drops:
                continue  # ❗ skip relic entirely if it has no mission drops

            output.append(f'{indent}  ↳ {relic_name} drops in:')

            for rd in mission_drops:
                sub = rd["subtype"] if rd["subtype"] else "Unknown"

                output.append(
                    f'{indent}    - Mission: {rd["source_name"]} | Rotation {sub} | {rd["rarity"]}'
                )

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
st.title("MyWarframeBrowser")

st.text("This is a Warframe item drop checker, its based on the information from the offical droptables, it might be a little slow but it works in real time")

stitem = st.text_input("Enter your item's name")

results = search_item(stitem)

if results:
    for r in results: 
        st.text(r)

