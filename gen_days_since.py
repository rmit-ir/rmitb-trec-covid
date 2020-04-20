import csv
from datetime import datetime
import json
from nested_lookup import nested_lookup
import subprocess

docids = set()
with open('docids.txt') as f:
    docids = set([line.rstrip() for line in f])

with open('dayssince.csv', 'w') as tfile:
    with open('badparse.csv', 'w') as badfile:
        with open('metadata.csv') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in spamreader:
                if row[0] in docids:
                    date = row[9]
                    try:
                        dateparse = datetime.strptime(date, '%Y-%m-%d')
                        # fix strange parser bug
                        if dateparse == datetime(2020, 12, 31):
                            dateparse.replace(year=2019)
                        now = datetime.now()
                        gap = (now - dateparse).days
                        if gap < 0:
                            gap = 0
                        tfile.write(row[0] + "," + str(gap) + "\n")
                    except ValueError as e:
                        try:
                            if date == "":
                                next
                            if date == "2020":
                                badfile.write(row[0] + "\n")
                            dateparse = datetime.strptime(date, '%Y')
                            now = datetime.now()
                            gap = (now - dateparse).days
                            tfile.write(row[0] + "," + str(gap) + "\n")
                        except ValueError as e:
                            # the 6--7 ones without a valid time parse all seem to talk about covid, so just set it to maximum
                            tfile.write(row[0] + "," + str(0) + "\n")
