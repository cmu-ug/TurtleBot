import json
import pprint

import boolean # BOOLEANPY - https://github.com/pauleve/boolean.py
algebra = boolean.BooleanAlgebra()

with open("fall_courses.json", "r") as f:
    fall_courses = json.load(f)

with open("spring_courses.json", "r") as f:
    spring_courses = json.load(f)

prereqs = {}

def isvalidcourse(x):
    return len(x) == 6 and x[0].isdigit() and x[1].isdigit() and x[2] == "-" and x[3].isdigit() and x[4].isdigit() and x[5].isdigit()

all_courses = {**fall_courses["courses"], **spring_courses["courses"]}

for courseid, data in all_courses.items():
    if data["prereqs"]:
        print(data["prereqs"], data["prereqs_obj"])
        prereqs_str = "".join([x for x in data["prereqs"] if x in " 0123456789-_"])
        prereqs_course = [x.strip() for x in prereqs_str.split(" ") if isvalidcourse(x.strip())]

        prereqs[courseid] = prereqs_course

print(prereqs)

