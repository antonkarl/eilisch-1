from pathlib import Path
from corpus_extrator import CorpusExtractor
from utils import TASK_TYPES


def main():
    basedir = Path("..")
    data_dir = basedir / "data"
    corpus_dir = data_dir / "IGC-Parla-22.10.ana"
    metadata_file = corpus_dir / "IGC-Parla-22.10.ana.xml"
    speech_type_file = data_dir / "speech_types.tsv"
    phonetic_dict_file = data_dir / "ice_pron_dict_north_clear.csv"
    frequency_list = data_dir / "frequency_lists" / "giga_simple_freq.json"

    # althingiFiles = list(Path(corpus_dir).rglob("*.xml"))
    year = "2019"
    althingiFiles = list(Path(corpus_dir / year).rglob("*.xml"))

    task_type = TASK_TYPES[1]

    corpus = CorpusExtractor(
        metadata_file,
        speech_type_file,
        phonetic_dict_file,
        frequency_list,
        task_type,
    )
    corpus.process_files(althingiFiles)
    data = corpus.data
    print(data.head())

    # metadata = get_metadata(
    #     metadata_file, speech_type_file, phonetic_dict_file, frequency_list
    # )

    # rows = []
    # for path in tqdm(althingiFiles, desc=f"Extracting {task_type} data"):
    #     results = examineFile(path, metadata, task_type=task_type)
    #     rows.extend(results)

    # save_path = data_dir / task_type
    # save_path.mkdir(parents=True, exist_ok=True)

    # data = pd.DataFrame(rows)
    # data.to_csv(
    #     save_path / f"{task_type}.tsv", sep="\t", index=False, header=headers[task_type]
    # )


if __name__ == "__main__":
    main()
