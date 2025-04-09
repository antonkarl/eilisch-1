import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from pathlib import Path
import pandas as pd
from tqdm import tqdm
import sys

base_dir = Path("..").resolve()
if str(base_dir) not in sys.path:
    sys.path.append(str(base_dir))

from collectmp import get_frq_dict, TEI_NS, check_sentence, Token, TASK_TYPES



corpus_path = Path("/Volumes/T9/IGC")
news_sources = {}

for entry in corpus_path.iterdir():
    if entry.is_dir():
        for folder in entry.iterdir():
            if folder.is_dir():
                news_sources[folder.stem] = folder


def get_metadata(freq_list):
    return {
        "freq_dict": get_frq_dict(freq_list)
    }

def get_article_data(article: Element):
    keywords = article.find(".//tei:keywords", TEI_NS)
    if keywords:
        terms = keywords.findall(".//tei:term", TEI_NS)
        terms = [term.attrib['sameAs'][1:] for term in terms]

        terms = "/".join(terms)
        # print(terms)
        
    analytic = article.find(".//tei:analytic", TEI_NS)
    title = analytic.find(".//tei:title", TEI_NS).text
    author = analytic.find(".//tei:author", TEI_NS)
    if author is None:
        author = "oflokkad"
    else:
        author = author.text

    date = analytic.find(".//tei:date", TEI_NS).attrib['when']

    # print(title, author, date)


    return terms, title, author, date

def check_article(article: Element, metadata, task_type):
    text = article.findall(".//tei:text", TEI_NS)
    if len(text) < 1:
        return
    
    rows = []
    terms, title, author, date = get_article_data(article)
    for asentence in article.findall(".//tei:s", TEI_NS):
        sentence = []
        for aword in asentence.iter():
            element_tag = aword.tag.split("}")[-1]
            if element_tag in ["w", "pc"]:
                word = aword.text
                if element_tag == "w":
                    lemma = aword.get("lemma")
                else:
                    lemma = "NONE"
                tag = aword.get("pos")
                token = Token(word, lemma, tag)
                sentence.append(token)

        full_text = " ".join([str(token.word) for token in sentence])
        results = check_sentence(sentence, task_type, metadata)

        for result in results:
            data = [
                date,
                metadata['source'],
                title,
                terms,
                author,
                *result,
                full_text,
            ]

            rows.append(data)
    return rows


HEADERS = ['date', 'source', 'title', 'categories', 'author', 'is_stylized', 'relevant_text', 'finite_verb', 'non-finite_verb', 'nfv_freq', 'full_text']
freq_list = Path(base_dir) / "data" / "frequency_lists" / "giga_simple_freq.json"
data_dir = Path("./data")

task_type = TASK_TYPES[1]
rows = []
# for source in sorted(news_sources.keys())[0:]:
for source in sorted(news_sources.keys()):
    source_path = news_sources[source]
    # metadata_file = source_path / f"IGC-News1-{source}-22.10.ana.xml"
    metadata = get_metadata(freq_list)
    metadata["source"] = source


    # rows = []
    files = [file for file in source_path.rglob('*.xml')]
    for file in tqdm(files, desc=f"Collecting news from {source}"):
        article = ET.parse(file).getroot()
        results = check_article(article, metadata, task_type)
        if results:
            rows.extend(results)


    save_path = data_dir / task_type
    save_path.mkdir(parents=True, exist_ok=True)

data = pd.DataFrame(rows)
data.to_csv(save_path / f"{task_type}.tsv", sep="\t", index=False, header=HEADERS)


