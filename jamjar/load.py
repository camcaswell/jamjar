
""" Disclaimer: I half-assed this for testing purposes.
    If you're using it for something important, at least look over it first.
"""

import csv
from datetime import datetime, timedelta
import re
import pytz
from person import Person

EXP_TRANS = {
    "none": 1,
    "some experience": 2,
    "a lot of experience": 3,
}


def parse_tz(raw_answer):
    location = re.match(r"(.+) \([A-Z]+\)", raw_answer).groups()[0]
    timezone = pytz.timezone(location)
    return timezone.utcoffset(datetime.now()) / timedelta(hours=1)


def load_data(filename='../Code_Jam_test_data.csv'):
    with open(filename, newline='') as file:
        reader = csv.reader(file)
        next(reader)
        people = []
        for idx, row in enumerate(reader):
            id = int(row[1])
            tz = parse_tz(row[4])
            exp = EXP_TRANS[row[6].strip().lower()]
            t2 = row[7].strip().lower() in ('yes',)
            t1 = row[8].strip().lower() in ('yes', "i don't mind either way")
            p = Person(id, tz, exp, t1, t2)
            people.append(p)
    return set(people)
