import csv
import json
from nested_lookup import nested_lookup
import subprocess

docids = set()
with open('docids.txt') as f:
    docids = set([line.rstrip() for line in f])

with open('./trec-covid/doc-text.trec', 'w') as tfile:
    with open('metadata.csv') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:
            if row[0] in docids:
                dups = row[1].split(";")
                paths = [line[2:] for line in subprocess.check_output("find . -type f \( -name '" + row[5] + ".xml.json' -o -name " + dups[0] + ".json \)", shell=True).splitlines()]
                tfile.write("<DOC>")
                tfile.write("<DOCNO>")
                tfile.write(row[0])
                tfile.write("</DOCNO>")
                tfile.write("<TITLE>")
                tfile.write(row[3])
                tfile.write("</TITLE>")
                tfile.write("<DATE>")
                tfile.write(row[9])
                tfile.write("</DATE>")
                tfile.write("<TEXT>")
                tfile.write(row[8]) # include abstract in body as PMC doesnt have it
                tfile.write("\n")
                if len(paths) >= 1:
                    with open(paths[0]) as f:
                        data = json.load(f)
                    textdata = "\n".join(nested_lookup('text', data))
                    tfile.write(textdata.encode('utf8'))
                tfile.write("</TEXT>")
                tfile.write("</DOC>")
