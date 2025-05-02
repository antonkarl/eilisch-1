import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import re

base_dir = Path(__file__).parent
xml_dir = base_dir / "IGC-Parla-22.10.ana"
training_dir = base_dir / "training_data"
speech_type_file = base_dir / "speech_types.tsv"

ns = {"tei": "http://www.tei-c.org/ns/1.0"}

speech_types = pd.read_csv(speech_type_file, sep="\t", index_col=0, header=0, names=["type"])
speech_types.index = speech_types.index.str.replace("https", "http")
speech_types = speech_types.to_dict()['type']

def match_source(source: str) -> str:
    try:
        base_source = source.split("?")[0]
        speech_type = speech_types[base_source]
    except KeyError:
        try:
            results = re.findall(r"=(\d+)", source)
            if results:
                base_source = f"http://www.althingi.is/altext/raeda/{results[0]}/{results[1]}.html"
                speech_type = speech_types[base_source]
            else:
                speech_type = "none"
        except KeyError:
            speech_type = "none"
    
    return speech_type

def get_speeches(file):
    root = ET.parse(file).getroot()
    speeches = root.findall(".//tei:u", ns)

    rows = []

    if speeches:
        for speech in speeches:
            speech_text = []
            speech_source = speech.attrib["source"]
            speech_type = match_source(speech_source)
            sentances = speech.findall(".//tei:s", ns)

            for s in sentances:
                sentance_text = []

                for token in s.iter():
                    tag = token.tag.split("}")[-1]

                    if tag in ["w", "pc"]:
                        word = token.text
                        sentance_text.append(word)

                speech_text.append(" ".join(sentance_text))
            
            rows.append((" ".join(speech_text), speech_type))
    
    return rows


            
        

file_list = list(xml_dir.rglob("*.xml"))
# file_list = list((xml_dir / '2016').rglob("*.xml"))

rows = []
# for file in tqdm(file_list):
#     results = get_speeches(file)
#     rows.extend(results)
results = get_speeches("/Users/atlisa/Projects/mal_og_taekni/eilisch/IGC-Parla-22.10.ana/1993/IGC-Parla_1993-03-09-124.ana.xml")
rows.extend(results)

data = pd.DataFrame(rows, columns=["text", "type"])
print(data)
data.to_csv(training_dir / "speech_types_test.tsv", sep="\t", index=False)