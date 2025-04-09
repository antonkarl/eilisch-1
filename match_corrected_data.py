# %%
import pandas as pd
from pathlib import Path
from collections import defaultdict

base_path = Path("/Users/atlisa/Projects/mal_og_taekni/eilisch")
data_path = base_path / "parsed_data"
indiv_path = data_path / "individuals"
corrected_path = base_path / "corrected_mps"
matched_path = corrected_path / "matched_data"
matched_path.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(data_path / "all_data.tsv", sep="\t")

columns = [7, 8, 9, 10, 15]
names = ["correction", "comment", "here", "text", "source"]
col_names = {old: new for old, new in zip(columns, names)}


def change_old_code(
    row: pd.Series, code_col: str | int, old_col: str | int
) -> pd.DataFrame:
    if int(row[old_col]) == 1:
        return row[code_col]
    elif int(row[old_col]) == 0:
        return abs(int(row[code_col]) - 1)
    elif int(row[old_col]) == -1:
        return -1
    return row[old_col]


def get_corrections(corrected_mp, all_mp):
    already_matched = defaultdict(list)
    group = all_mp[all_mp["speech_source"].isin(corrected_mp["source"])]

    new_data = {"correction": [], "comment": [], "here": []}

    for _, row in group.iterrows():
        source = row["speech_source"]
        rel_text = row["relevant_text"]
        matches = corrected_mp[corrected_mp["source"] == source]
        label = comment = h = None
        if matches.empty:
            new_data["correction"].append(None)
            new_data["comment"].append(None)
            new_data["here"].append(None)
            continue

        if len(matches) > 1:
            for i, (_, match) in enumerate(matches.iterrows()):
                if (match["text"] == rel_text) and (i not in already_matched[source]):
                    already_matched[source].append(i)
                    label = match["correction"]
                    comment = match["comment"]
                    h = match["here"]
        elif matches["text"].values[0] == rel_text:
            label = matches["correction"].values[0]
            comment = matches["comment"].values[0]
            h = matches["here"].values[0]

        new_data["correction"].append(label)
        new_data["comment"].append(comment)
        new_data["here"].append(h)

    return new_data


mp_dfs = {}
DNF = ["upptaka fannst ekki", "DNF", "ekki hægt að hlusta"]
for file in corrected_path.glob("*.tsv"):
    person = file.stem
    mp_df = pd.read_csv(file, sep="\t", header=None)
    mp_df = mp_df[columns].rename(columns=col_names)
    condition = ~((mp_df["correction"].isna()) & (mp_df["comment"].isna()))
    all_mp = df[df["person"] == person]
    mp_df = mp_df[condition]
    mp_df["comment"] = mp_df["comment"].apply(lambda x: "DNF" if x in DNF else x)
    mp_df["correction"] = mp_df.apply(
        lambda x: "xxx" if x["comment"] == "DNF" else x["correction"], axis=1
    )

    filtered_mp = all_mp[all_mp["speech_source"].isin(mp_df["source"])].reset_index(
        drop=True
    )
    mismatch = mp_df[~mp_df["source"].isin(all_mp["speech_source"])]
    print(person)
    print("\tNr. of corrections not in script data:", len(mismatch))
    print()

    matched_data = get_corrections(mp_df, filtered_mp)
    matched_data_df = pd.DataFrame(matched_data)
    concat_data = pd.concat([filtered_mp, matched_data_df], axis=1)
    mp_dfs[person] = concat_data


for person, data in mp_dfs.items():
    if data["correction"].dtype == "float64":
        data["correction"] = data["correction"].astype("Int64")
    data.to_csv(matched_path / f"{person}.tsv", sep="\t", index=False)
