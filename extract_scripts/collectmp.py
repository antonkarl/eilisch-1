from pathlib import Path
from corpus_extrator import CorpusExtractor
from utils import TASK_TYPES, SaveConfig

TEST = False

def main():
    basedir = Path("..")
    extraction_data_dir =  Path("./extraction_data")
    data_dir = basedir / "data"
    corpus_dir = data_dir / "IGC-Parla-22.10.ana"
    metadata_file = corpus_dir / "IGC-Parla-22.10.ana.xml"
    speech_type_file = extraction_data_dir / "speech_types.tsv"
    phonetic_dict_file = extraction_data_dir / "ice_pron_dict_north_clear.tsv"
    frequency_list = extraction_data_dir / "giga_simple_freq_2.json"
    saved_speeches = data_dir / "formality_test"

    task_type = TASK_TYPES[2]
    # config = SaveConfig(saved_speeches, [2000, 2021], "THorgerdurGunnarsdottir"

    configs = [
        SaveConfig(person="LogiEinarsson", timespans=[[2010, 2021]]),
        SaveConfig(person="IngaSaeland", timespans=[[2017,2021]]),
        SaveConfig(person="KristjanJuliusson", timespans=[[2007, 2021]]),
        SaveConfig(person="BjornGislason1959", timespans=[[1990, 2017]]),
        SaveConfig(person="ValgerdurGunnarsdottir1955", timespans=[[2013, 2020]]),
        SaveConfig(person="BjarkeyGunnarsdottir", timespans=[[2004, 2021]]),
        SaveConfig(person="BirkirJonsson", timespans=[[2003, 2013]]),
        SaveConfig(person="HoskuldurTHorhallsson", timespans=[[2007, 2016]]),
        SaveConfig(person="AnnaArnadottir", timespans=[[2017,2021]]),
    ]

    if TEST:
        save_path = data_dir / "tests"
        year = "2019"
        althingiFiles = list(Path(corpus_dir / year).rglob("*.xml"))
    else:
        save_path = data_dir / task_type / "individuals"
        althingiFiles = list(Path(corpus_dir).rglob("*.xml"))



    for config in configs:
        print(f"Extracting {task_type} from", config.person)


        corpus = CorpusExtractor(
            metadata_file,
            speech_type_file,
            phonetic_dict_file,
            frequency_list,
            task_type,
            save_data=config
        )
        corpus.process_files(althingiFiles)

        corpus.save_results(save_path, config.person)


if __name__ == "__main__":
    main()
