from bs4 import BeautifulSoup, Tag
import pandas as pd
import requests
from tqdm import tqdm
import re

MAIN_URL = "https://www.althingi.is/thingstorf/raedur/raedur-thingmanna-eftir-thingum/"
BASE_URL = "https://www.althingi.is"

CATEGORIES = ["um fundarstjórn", "óundirbúinn fyrirspurnatími"]

PATTERN = r"(?:\S+ ){3}(?:kl\. \d{1,2}:\d{2} )?(.*)"


def scrape_urls(url):
    hrefs = []
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    list_body = soup.find_all("div", {"class": "article"})[0]
    anchors = list_body.find_all("a")
    for a in anchors:
        href = a.get("href")
        hrefs.append(MAIN_URL + href)

    return hrefs


def scrape_speech_types(url):
    url_dict = {}
    tags = ["p", "li"]
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    speech_list = soup.find_all("div", {"class": "article"})[0]
    tag_list: tuple[Tag] = speech_list.find_all(tags)

    p_type = ""
    for tag in tag_list:
        speech_type = ""
        if tag.name == "p":
            p_type = tag.text.split(")")[-1]

        if tag.name == "li":
            a = tag.find("a")
            href = a.get("href")
            try:
                href = BASE_URL + href
            except TypeError:
                print(href)

            if p_type not in CATEGORIES:
                match = re.search(PATTERN, a.text)
                speech_type = match.group(1)
            else:
                speech_type = p_type

            url_dict[href] = speech_type

    return url_dict


if __name__ == "__main__":
    url_dict = {}
    list_of_parliaments = scrape_urls(MAIN_URL)
    for parla in tqdm(list_of_parliaments):
        mp_list = scrape_urls(parla)
        for mp in tqdm(mp_list):
            results = scrape_speech_types(mp)
            url_dict.update(results)

    data = pd.Series(url_dict)
    data.to_csv("./speech_types_original.tsv", sep="\t", header=False)
