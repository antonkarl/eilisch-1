# How to Use the `collectmp_cli.py` CLI Tool
This CLI tool processes IGC-PARLA corpus files and extracts stylistic fronting or hardspeech data into a TSV file. It uses metadata, speech types, phonetic dictionaries, and frequency dictionaries to analyze the corpus.

## Usage
Install the requirements (use python3.12). 
```bash
pip install requirements.txt
```

Download necessary files [here](https://drive.google.com/uc?export=download&id=1-acd-uzqOiJU3IYwv3lIZSKEFX5dXTBb) and extract them into the `extract_scripts` folder. The name of the extracted folder should be `extraction_data`.

Run the script from the command line:

```bash
python collectmp_cli.py <xml_path> [options]
```

### Required Argument
- `xml_path`: Path to a directory containing XML files or a single XML file to process.

### Optional Arguments
- `--task-type`: Type of data to extract. Defaults to `sf_main_clause`. Options include:
	- `sf_main_clause`: Extract stylistic fronting in main clauses.
	- `sf_sub_clause`: Extract stylistic fronting in sub-clauses.
	- `hardspeech`: Extract hardspeech patterns.
- `--metadata`: Path to an XML metadata file. Defaults to `IGC-Parla-22.10.ana.xml` located in the archive directory.
- `--speech-types`: Path to a TSV file for speech types. Defaults to `extraction_data/speech_types.tsv`.
- `--freq-dict`: Path to a word frequency dictionary. Defaults to `extraction_data/giga_simple_freq_2.json`.
- `--phonetic-dict`: Path to a phonetic dictionary. Defaults to `extraction_data/ice_pron_dict_north_clear.tsv`.
- `--out-path`: Directory to save the output TSV file. Defaults to the current working directory.
- `--config-file`: Path to a JSON configuration file. This file can specify additional filtering options, such as years or specific individuals.

### Example Commands

1. Process a directory of XML files:
```bash
python collectmp_cli.py /path/to/xml/files --task-type sf_main_clause --out-path /path/to/output
```
2. Process a single XML file with custom metadata:
```bash
python collectmp_cli.py /path/to/file.xml --metadata /path/to/metadata.xml --out-path /path/to/output
```
3. Extract hardspeech data:
```bash
python collectmp_cli.py /path/to/xml/files --task-type hardspeech
```
4. Use a configuration file to filter results:
```bash
python collectmp_cli.py /path/to/xml/files --config-file /path/to/config.json --out-path /path/to/output
```

### Output
The tool generates a TSV file in the specified output directory. The headers of the TSV file depend on the task type:

- For `sf_main_clause` and `sf_sub_clause`, the headers include:
	- `year`, `date`, `speech_type`, `person`, `sex`, `year_born`, `role`, `speaker_type`, `party_id`, `party_name`, `party_status`, `gov`, `is_stylized`, `relevant_text`, `finite_verb`, `non-finite_verb`, `nfv_freq`, `mattr_<window_size>`, `word_rank_mean`, `word_rank_median`, `speech_word_count`, `full_text`, `speech_source`, `speech_id`.
- For `hardspeech`, the headers include:
	- `year`, `date`, `speech_type`, `person`, `sex`, `year_born`, `role`, `speaker_type`, `party_id`, `party_name`, `party_status`, `gov`, `before`, `word`, `after`, `is_hardspeech`, `plosive`, `lemma`, `pos`, `word_freq`, `mattr_<window_size>`, `word_rank_mean`, `word_rank_median`, `speech_word_count`, `full_text`, `speech_source`, `speech_id`.

### Notes
- Ensure all required files (e.g., metadata, speech types, dictionaries) exist in the specified paths.
- The output directory must exist before running the tool.
- The tool uses the following default files from the `utils.py` configuration:
	- Metadata file: `IGC-Parla-22.10.ana.xml`
	- Speech types file: `extraction_data/speech_types.tsv`
	- Phonetic dictionary: `extraction_data/ice_pron_dict_north_clear.tsv`
	- Frequency dictionary: `extraction_data/giga_simple_freq_2.json`.
 
## Config file

### Example

```json
{
  "configs": [
    {
      "person": "SteingrimurSigfusson",
      "years": [2013],
      "timespans": [[1992, 2000], [2016, 2020]],
      "save_path": "./full_speeches"
    },
    {
      "person": "IngaSaeland",
      "save_path": "./full_speeches" 
    }
  ]
}
```

### Config options

Each object represents a configuration for a specific person and may include the following properties:
- `"person"`: A string representing the name of the person (e.g., `"SteingrimurSigfusson"`, `"IngaSaeland"`).
- `"years"`: An array of integers representing specific years of interest (e.g., `[2013]`).
- `"timespans"`: An array of arrays, where each inner array represents a range of years (e.g.,` [[1992, 2000], [2016, 2020]]`).
- `"save_path"`: A string representing the path where data (e.g., speeches) should be saved (e.g., `"./full_speeches"`). If omitted the speeches are not saved.

All properties are optional.

# File Overview: `extract_scripts` Folder

| File/Folder            | Description                                                                                   |
|------------------------|----------------------------------------------------------------------------------------------|
| `collectmp_cli.py`     | Main CLI tool for processing IGC-PARLA corpus files. Handles argument parsing and extraction.|
| `collectmp.py`         | Batch extraction script for testing or bulk processing with hardcoded configurations.         |
| `corpus_extrator.py`   | Contains the `CorpusExtractor` class for metadata loading and corpus file processing.         |
| `file_handler.py`      | Defines `FileHandler` for parsing XML files and extracting speeches and speaker metadata.     |
| `speech.py`            | Implements the `Speech` class for analyzing and extracting features from individual speeches. |
| `utils.py`             | Shared constants, helper functions, and data structures used across scripts.                 |
| `config.json`          | Example configuration file specifying extraction targets and save paths.                      |
| `extraction_data/`     | Directory containing required data files (dictionaries, mappings) for extraction.             |