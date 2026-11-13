"""Gradebook validation and year-end rules; independent of persistence."""
import re

from flask import abort

PROGRAMS = {"a": "Paket A", "b": "Paket B", "c-ipa": "Paket C IPA", "c-ips": "Paket C IPS"}
CLASSES = {"a": "I II III IV V VI", "b": "VII VIII IX", "c-ipa": "X XI XII", "c-ips": "X XI XII"}
SEMESTERS = ("Ganjil", "Genap")


def prepare_next_year(state, program, year):
    grades = CLASSES[program].split()
    rosters = {grade: [] for grade in grades}
    count = 0
    for i, grade in enumerate(grades):
        group = state["c"][grade]
        for student in group["st"]:
            decision = student.get("decision")
            if not student.get("nama", "").strip() or not decision:
                abort(422)
            if decision == "Lulus" and grade == grades[-1]:
                continue
            if decision == "Tinggal kelas":
                target = grade
            elif decision == "Naik kelas" and grade != grades[-1]:
                target = grades[i+1]
            else:
                abort(422)
            identity = {k:v for k,v in student.items() if k not in ("n", "decision", "norap")}
            rosters[target].append(identity)
            count += 1
        group.update(tahun=f"{year+1}/{year+2}", wali="", nip="", naik="")
        for semester in group["ms"].values():
            semester["tgl"] = ""
    if not count:
        abort(422)
    for grade, group in state["c"].items():
        group["st"] = rosters[grade]
    state["sch"].update(kelas=grades[0], sem="Ganjil")


def subject_key(name):
    return re.sub("[^a-z0-9]", "", name.lower())


def validate(state, program, year):
    def strings(obj, keys):
        return isinstance(obj, dict) and all(isinstance(obj.get(k), str) and len(obj[k]) <= 4000 for k in keys.split())

    def number(value):
        return type(value) in (int,float) and 0 <= value <= 100

    try:
        grades = CLASSES[program].split()
        school = state["sch"]
        assert_valid = (strings(school, "nama npsn a1 a2 a3 ar pos web email tel kepala nipk tempat")
                        and school["kelas"] in grades and school["sem"] in SEMESTERS and set(state["c"]) == set(grades)
                        and type(state.get("rows",30)) is int and 1 <= state.get("rows",30) <= 1000)
        logo = state["logo"]
        if not assert_valid or not isinstance(logo,str) or (logo and not re.fullmatch(r"data:image/png;base64,[A-Za-z0-9+/]+=*",logo)):
            abort(422)
        for grade, group in state["c"].items():
            if not isinstance(group,dict) or not strings(group, "wali nip naik tahun") or group["tahun"] != f"{year}/{year+1}" or set(group["ms"]) != set(SEMESTERS):
                abort(422)
            for m in group["ms"].values():
                if not program.startswith("c") and m.get("p") != []:
                    abort(422)
                if not strings(m,"tgl") or not number(m["batas"]) or not isinstance(m["e"],list) or len(m["e"]) > 30 or not all(strings(e,"n p k") for e in m["e"]):
                    abort(422)
                names = set()
                for k in (("u","p","k") if program.startswith("c") else ("u","k")):
                    if not isinstance(m[k],list) or len(m[k]) > 80:
                        abort(422)
                    for r in m[k]:
                        if not strings(r,"n a b") or not number(r["kkm"]) or r["sp"] not in (0,1):
                            abort(422)
                        if r["n"]:
                            key = subject_key(r["n"])
                            if not key or key in names or key in ("izin","sakit","alpa","constructor","prototype"):
                                abort(422)
                            names.add(key)
            if not isinstance(group["st"],list) or len(group["st"]) > 1000:
                abort(422)
            for student in group["st"]:
                if not isinstance(student,dict) or set(student) - set("nama nipd nisn jk tl tgl agama alamat norap anak tel dk dtg ayah ibu kayah kibu wali kwali n decision".split()) or not all(isinstance(v,str) and len(v)<=4000 for k,v in student.items() if k!="n"):
                    abort(422)
                if student.get("decision", "") not in ("", "Tinggal kelas", "Lulus" if grade == grades[-1] else "Naik kelas"):
                    abort(422)
                for sem, scores in student.get("n",{}).items():
                    if sem not in SEMESTERS or not isinstance(scores,dict):
                        abort(422)
                    for k,v in scores.items():
                        if re.fullmatch(r"e[0-9]{1,2}",k) and isinstance(v,str) and len(v)<=40:
                            continue
                        if k == "catatan" and isinstance(v,str) and len(v)<=4000:
                            continue
                        if not re.fullmatch(r"(?:[upk][0-9]{1,2}|izin|sakit|alpa)",k):
                            abort(422)
                        if not isinstance(v,str) or len(v)>12 or (v and (not re.fullmatch(r"[0-9]+(?:[.][0-9]+)?",v) or (not v.isdigit() if k in ("izin","sakit","alpa") else not 0<=float(v)<=100))):
                            abort(422)
    except (KeyError, TypeError, AttributeError, ValueError, OverflowError):
        abort(422)
