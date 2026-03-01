import csv, json, os
from app.schemas import Item
from app.report import build_report

def load_csv(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for i, row in enumerate(r):
            uid = row.get("id") or f"u{i+1}"
            text = (row.get("bio") or row.get("text") or "").strip()
            if text:
                rows.append(Item(id=uid, text=text))
    return rows

def main():
    in_path = os.path.join("data", "sample_bios.csv")
    out_path = os.path.join("data", "report.json")
    items = load_csv(in_path)
    rep = build_report(items)
    os.makedirs("data", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rep.model_dump(), f, ensure_ascii=False, indent=2)
    print(f"Wrote {out_path} with total={rep.total}")

if __name__ == "__main__":
    main()
