from bs4 import BeautifulSoup
import json
import csv
from pathlib import Path


def clean_text(tag):
    if not tag:
        return ""
    return " ".join(tag.get_text().split())


def extract_hierarchy(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    hierarchy = []

    systems = soup.find_all("div", style=lambda v: v and "#666666" in v)

    for system_div in systems:
        system_name = clean_text(system_div.find("b"))
        system_id = system_div.get("id", "")

        system_node = {"name": system_name, "type": "System", "categories": []}

        container_id = system_id.replace("treeitem", "treecontainer")
        system_container = soup.find("div", id=container_id)

        if system_container:
            categories = system_container.find_all("div", style=lambda v: v and "lightblue" in v, recursive=False)

            for cat_div in categories:
                cat_name = clean_text(cat_div.find("b"))
                cat_id = cat_div.get("id", "")

                cat_node = {"name": cat_name, "type": "Category", "subcategories": []}

                cat_container_id = cat_id.replace("treeitem", "treecontainer")
                cat_container = system_container.find("div", id=cat_container_id)

                if cat_container:
                    sub_cats = cat_container.find_all("div", style=lambda v: v and "#999999" in v, recursive=False)

                    for sub_div in sub_cats:
                        sub_name = clean_text(sub_div.find("b"))
                        sub_id = sub_div.get("id", "")

                        sub_node = {"name": sub_name, "type": "Subcategory", "reports": []}

                        sub_container_id = sub_id.replace("treeitem", "treecontainer")
                        sub_container = cat_container.find("div", id=sub_container_id)

                        if sub_container:
                            reports = sub_container.find_all("div", style=lambda v: v and "#FFFFFF" in v, recursive=False)

                            for rep_div in reports:
                                code = clean_text(rep_div.find("div", class_="treeitemauxText"))
                                title = clean_text(rep_div.find("b"))

                                sub_node["reports"].append({"code": code, "title": title})

                        cat_node["subcategories"].append(sub_node)

                system_node["categories"].append(cat_node)

        hierarchy.append(system_node)

    return hierarchy


def hierarchy_to_csv_rows(hierarchy):
    """Flatten hierarchy into CSV rows"""
    rows = []

    for system in hierarchy:
        for category in system["categories"]:
            for subcategory in category["subcategories"]:
                for report in subcategory["reports"]:
                    rows.append(
                        {
                            "System": system["name"],
                            "Category": category["name"],
                            "Subcategory": subcategory["name"],
                            "Report Code": report["code"],
                            "Report Title": report["title"],
                        }
                    )

    return rows


# ---------- File handling ----------
html_path = Path(r"downloads\24-02-2026\16\ClinicReport.html")
json_path = html_path.with_suffix(".json")
csv_path = html_path.with_suffix(".csv")

with html_path.open("r", encoding="utf-8") as f:
    html_doc = f.read()

report = extract_hierarchy(html_doc)

# Save to JSON
with json_path.open("w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

# Save to CSV
csv_rows = hierarchy_to_csv_rows(report)

with csv_path.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "System",
            "Category",
            "Subcategory",
            "Report Code",
            "Report Title",
        ],
    )
    writer.writeheader()
    writer.writerows(csv_rows)

print(f"Hierarchy saved to JSON: {json_path}")
print(f"Hierarchy saved to CSV: {csv_path}")
