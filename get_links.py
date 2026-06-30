import requests
from bs4 import BeautifulSoup
from util import *

url = input("Input FitGirl game page: ")
include = input("Input selective/optional contents (, for separator eg: 'eng,english'. leave blank to download all): ")
if include != "":
    include = include.split(",")
    include = [_.replace(" ","") for _ in include]
    print(include)
else: lang = False

try:
    game_name = url.replace("https://", "").split("/",1)[1].replace("/","")
except IndexError:
    game_name = "links"
    LogWarning(f"Error parsing game name, defaulting to '{game_name}'")

page = requests.get(url)

if page.status_code != 200:
    LogError(f"HTTP ERROR {page.status_code}")
    print(page.text)
    quit(page.status_code)

soup = BeautifulSoup(page.text, "html.parser")

links = [
    a["href"]
    for dlinks_div in soup.find_all("div", class_="dlinks")
    for a in dlinks_div.find_all("a", href=True)
    if a["href"].startswith("https://fuckingfast.co/")
]

LogInfo(f"Found {len(links)} link(s)")

count = 0
with open(f"{game_name}.txt", "w") as f:
    for l in links:
        if ("selective" in l.lower() or "optional" in l.lower()) and include != False:
            if any(_ in l.lower() for _ in include):
                f.write(l+"\n")
                count+=1
        else:
            f.write(l+"\n")
            count+=1

LogInfo(f"{count} out of {len(links)} link(s) written to {game_name}.txt")