import json, sys, pathlib

SRC = pathlib.Path("data/petrecords.jsonl")
ANC = pathlib.Path("data/anchors.json")
OUT = pathlib.Path("data/petrecords.merged.jsonl")

anchors = {a["id"]: a for a in json.loads(ANC.read_text())}

with SRC.open() as fin, OUT.open("w") as fout:
    for line in fin:
        if not line.strip(): 
            continue
        rec = json.loads(line)
        a = anchors.get(rec.get("id"))
        if a:
            rec["onChainTxHash"] = a["onChainTxHash"]
            rec["onChainCid"] = a["onChainCid"]
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"wrote {OUT}")
