
import xml.etree.ElementTree as ET
import sys
import os

# Add backend to path to import app modules if needed, 
# but here we just want to test the logic extracted from import_project.py
# to see if it correctly finds PredecessorLink

def _parse_duration(val):
    return 0.0

def _parse_date(val):
    return None

def _norm_priority(val):
    return "Medium"

def _xml_text(el, tag):
    child = el.find(tag)
    return child.text if child is not None and child.text else None

def parse_xml_debug(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    root = ET.fromstring(content)
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    print(f"Detected Namespace: '{ns}'")

    task_elements = (
        root.findall(f".//{ns}Tasks/{ns}Task")
        or root.findall(f".//{ns}Task")
        or root.findall(".//Tasks/Task")
        or root.findall(".//Task")
        or root.findall(".//task")
    )

    print(f"Found {len(task_elements)} tasks.")

    for te in task_elements:
        uid = _xml_text(te, f"{ns}UID") or _xml_text(te, "UID") or ""
        name = _xml_text(te, f"{ns}Name") or _xml_text(te, "Name") or ""
        
        print(f"Task: {name} (UID: {uid})")
        
        # Debug Predecessor Linking
        preds = te.findall(f"{ns}PredecessorLink")
        print(f"  - Raw PredecessorLink count (NS='{ns}'): {len(preds)}")
        
        if len(preds) == 0:
             # Try without namespace if failed
             preds = te.findall("PredecessorLink")
             print(f"  - Raw PredecessorLink count (No NS): {len(preds)}")

        for pl in preds:
            pred_uid = _xml_text(pl, f"{ns}PredecessorUID") or _xml_text(pl, "PredecessorUID")
            print(f"  - Found PredecessorUID: {pred_uid}")

if __name__ == "__main__":
    parse_xml_debug("test_deps.xml")
