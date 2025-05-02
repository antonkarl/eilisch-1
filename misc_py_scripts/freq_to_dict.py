import pandas as pd
import json
from tqdm import tqdm
from pathlib import Path

def tsv_to_json(tsv_file, json_file):
    word_dict = {}

    df = pd.read_csv(tsv_file, sep="\t", names=["word", "tag", "freq"])

    for index, row in tqdm(df.iterrows(), total=len(df)):
        word = row['word']
        tag = row['tag']
        freq = int(row["freq"])

        if word not in word_dict:
            word_dict[word] = {}

        word_dict[word][tag] = freq, index + 1


    with open(json_file, "w", encoding="utf-8") as json_out:
        json.dump(word_dict, json_out, ensure_ascii=False, indent=4)



in_file = Path("./data/frequency_lists/giga_simple_freq.tsv")
out_file = Path("./data/frequency_lists/giga_simple_freq_2.json")

tsv_to_json(in_file, out_file)