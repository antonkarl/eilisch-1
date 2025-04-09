from numbers_parser import Document
import csv

doc = Document("./glf_files/agustagustsson-corrected.numbers")

sheet = doc.sheets[0]

print([row for row in sheet.tables[0].rows()])