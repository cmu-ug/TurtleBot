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
        prereqs_str = "".join([x for x in data["prereqs"] if x in " 0123456789-_"])
        prereqs_course = [x.strip() for x in prereqs_str.split(" ") if isvalidcourse(x.strip())]

        prereqs[courseid] = prereqs_course


postreqs = {}
postreqs2 = {}

for course, reqs in prereqs.items():
    for req in reqs:
        if req not in postreqs:
            postreqs[req] = []
            postreqs2[req] = []


        remain = all_courses[course]["prereqs"]
        remain = remain.replace(req, "TRUE").replace("-", "_")
        remain = str(algebra.parse(remain).simplify()).replace("|", " or ").replace("&", " and ").replace("_", "-")

        if remain == "1": remain = "None"

        postreqs[req].append(course)
        postreqs2[req].append(course + " - " + all_courses[course]["name"]+"\n`    Remaining prereqs: "+remain+"`\n")

for a in postreqs.keys():
    postreqs[a] = sorted(list(set(postreqs[a])))
    postreqs2[a] = sorted(list(set(postreqs2[a])))

with open("postreqs-verbose.json", "w+") as f:
    json.dump(postreqs2, f)
