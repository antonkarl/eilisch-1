from pathlib import Path
from corpus_extrator import CorpusExtractor
from utils import TASK_TYPES

TEST = False

def main():
    basedir = Path("..")
    data_dir = basedir / "data"
    corpus_dir = data_dir / "IGC-Parla-22.10.ana"
    metadata_file = corpus_dir / "IGC-Parla-22.10.ana.xml"
    speech_type_file = data_dir / "speech_types.tsv"
    phonetic_dict_file = data_dir / "ice_pron_dict_north_clear.csv"
    frequency_list = data_dir / "frequency_lists" / "giga_simple_freq.json"

    task_type = TASK_TYPES[1]

    if TEST:
        save_path = data_dir / "tests"
        year = "2019"
        althingiFiles = list(Path(corpus_dir / year).rglob("*.xml"))
    else:
        save_path = data_dir / task_type
        althingiFiles = list(Path(corpus_dir).rglob("*.xml"))



    corpus = CorpusExtractor(
        metadata_file,
        speech_type_file,
        phonetic_dict_file,
        frequency_list,
        task_type,
    )
    corpus.process_files(althingiFiles)

    corpus.save_results(save_path, f"new_{task_type}")


if __name__ == "__main__":
    main()
