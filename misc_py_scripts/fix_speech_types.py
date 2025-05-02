import re
import pandas as pd
import requests
from pathlib import Path
from bs4 import BeautifulSoup

filename = 'speech_types.tsv'
base_dir = Path(__file__).parent
filepath = base_dir / filename
PATTERN = r"kl\. \d{1,2}:\d{2} (.*)"

def change_cell(text):
    results = re.search(PATTERN, text)
    if results:
        return results.group(1)
    return text

if __name__ == "__main__":
    # df = pd.read_csv(filepath, sep="\t", index_col=0)
    # df = df.dropna()

    # test = "kl. 13:03 um andsvar"
    # test2 = "andsvar"

    # print(df.head())
    # # df['type'] = df['type'].apply(change_cell)

    # df.to_csv(base_dir / 'speech_types_cleaned.tsv', sep="\t", index=False)
    response = requests.get("http://www.althingi.is/altext/raeda/?lthing=82&rnr=2921")
    soup = BeautifulSoup(response.content, 'html.parser')
    elem = soup.find("link", {"rel": "canonical"})
    print(elem.attrs["href"].split("?")[0])