
import xml.etree.ElementTree as ET
import re
from typing import Optional, List, Dict, Any

# Copying the parse logic from import_project.py for isolation testing

def _xml_text(el, tag: str, alternatives: Optional[List[str]] = None) -> Optional[str]:
    """Find a tag or its alternatives and return text."""
    tags = [tag] + (alternatives or [])
    for t in tags:
        child = el.find(t)
        if child is not None and child.text:
            return child.text
    # Case-insensitive fallback for direct children
    tag_lower = tag.lower()
    for child in el:
        if child.tag.split('}')[-1].lower() == tag_lower:
            return child.text
    return None

def _parse_duration(val: str) -> float:
    return 0.0 # Mock

def _parse_date(val: Optional[str]):
    return None # Mock

def _norm_priority(val: Optional[str]) -> str:
    return "Medium"

def _parse_xml(content: str) -> dict:
    """Parse XML content. Supports MS Project XML format and generic XML."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")

    # Detect namespace
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    project_title = "Test Project"

    # Try various paths to find task elements
    task_elements = (
        root.findall(f".//{ns}Tasks/{ns}Task")
        or root.findall(f".//{ns}Task")
        or root.findall(".//Tasks/Task")
        or root.findall(".//Task")
        or root.findall(".//task")
    )

    tasks = []

    for te in task_elements:
        name = _xml_text(te, f"{ns}Name", ["Name", "name", "Title", "title", "Task", "task", "Activity", "activity"]) or ""
        uid = _xml_text(te, f"{ns}UID", ["UID", "uid", "ID", "id"]) or ""
        
        # Extract PredecessorLink elements
        preds_data = []
        # ERROR SUSPECT: Finding PredecessorLink
        links = te.findall(f"{ns}PredecessorLink") or te.findall("PredecessorLink") or []
        print(f"Task '{name}' (UID: {uid}) found {len(links)} links")
        
        for pl in links:
            pred_uid = _xml_text(pl, f"{ns}PredecessorUID") or _xml_text(pl, "PredecessorUID") or ""
            print(f"  - Link to {pred_uid}")
            if pred_uid:
                preds_data.append({
                    "uid": pred_uid,
                    "type": "FS",
                    "lag": 0
                })

        tasks.append({
            "title": name.strip(),
            "xml_uid": uid,          
            "predecessor_links": preds_data, 
        })

    return {"title": project_title, "tasks": tasks}

# Sample XML Data (MS Project format)
xml_content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Project xmlns="http://schemas.microsoft.com/project">
    <Name>Test Project</Name>
    <Tasks>
        <Task>
            <UID>1</UID>
            <ID>1</ID>
            <Name>Task A</Name>
        </Task>
        <Task>
            <UID>2</UID>
            <ID>2</ID>
            <Name>Task B</Name>
            <PredecessorLink>
                <PredecessorUID>1</PredecessorUID>
                <Type>1</Type>
                <CrossProject>0</CrossProject>
                <LinkLag>0</LinkLag>
                <LagFormat>7</LagFormat>
            </PredecessorLink>
        </Task>
    </Tasks>
</Project>
"""

# Run Test
print("Running _parse_xml test...")
result = _parse_xml(xml_content)
print("\nParsed Result:")
for t in result["tasks"]:
    print(f"Task: {t['title']} (UID: {t['xml_uid']}) - Preds: {len(t['predecessor_links'])}")

