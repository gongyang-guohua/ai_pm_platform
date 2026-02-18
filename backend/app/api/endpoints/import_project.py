"""
Project Import Endpoint
Supports: CSV, JSON, XML (MS Project XML), MPP (basic XML extraction)
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.models.project import Project, Task, Material, Risk
from app.schemas.project import Project as ProjectSchema
from app.core.database import get_db
import csv
import json
import io
import re
import xml.etree.ElementTree as ET
import traceback
from datetime import datetime
from typing import Optional, List, Dict, Any

router = APIRouter()


def _parse_csv(content: str) -> dict:
    reader = csv.DictReader(io.StringIO(content))
    tasks = []
    materials = []
    project_title = "Imported CSV Project"

    for row in reader:
        norm = {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items() if k}

        if norm.get("category") or norm.get("unit_price"):
            materials.append({
                "name": norm.get("name") or norm.get("title", "Unknown Material"),
                "category": norm.get("category", "General"),
                "quantity": _safe_float(norm.get("quantity", "0")),
                "unit": norm.get("unit", "pcs"),
                "unit_price": _safe_float(norm.get("unit_price", "0")),
                "total_price": _safe_float(norm.get("total_price", "0"))
                    or _safe_float(norm.get("quantity", "0")) * _safe_float(norm.get("unit_price", "0")),
            })
            continue

        title = (
            norm.get("title") or norm.get("task_name") or norm.get("activity_name")
            or norm.get("name") or norm.get("task") or "Untitled Task"
        )

        if not tasks and (norm.get("project") or norm.get("project_title")):
            project_title = norm.get("project") or norm.get("project_title") or project_title

        est = _safe_float(norm.get("estimated_hours") or norm.get("duration") or norm.get("hours") or "0")
        dep_str = norm.get("dependencies") or norm.get("predecessors") or ""
        deps = [d.strip() for d in dep_str.split(",") if d.strip()] if dep_str else []

        tasks.append({
            "wbs_code": norm.get("wbs") or norm.get("wbs_code") or None,
            "title": title,
            "description": norm.get("description") or norm.get("scope") or "",
            "estimated_hours": est,
            "priority": _norm_priority(norm.get("priority")),
            "status": _norm_status(norm.get("status")),
            "task_type": "milestone" if (norm.get("type") or "").lower() in ("milestone", "ms") else "task",
            "planned_start": _parse_date(norm.get("start") or norm.get("planned_start")),
            "planned_end": _parse_date(norm.get("end") or norm.get("planned_end") or norm.get("finish")),
            "responsible_party": norm.get("responsible") or norm.get("responsible_party") or norm.get("owner") or None,
            "dependencies_raw": deps,
            "is_summary": False,
            "outline_level": 1,
        })

    return {"title": project_title, "tasks": tasks, "materials": materials}


def _parse_json(content: str) -> dict:
    data = json.loads(content)
    if isinstance(data, list):
        return {"title": "Imported JSON Project", "tasks": data, "materials": []}
    return {
        "title": data.get("title") or data.get("project_title") or "Imported JSON Project",
        "tasks": data.get("tasks", []),
        "materials": data.get("materials", []),
        "description": data.get("description") or data.get("summary") or "",
        "industry": data.get("industry") or "",
    }


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

    project_title = (
        _xml_text(root, f"{ns}Name") or _xml_text(root, f"{ns}Title")
        or _xml_text(root, "Name") or _xml_text(root, "Title")
        or "Imported XML Project"
    )

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
        name = _xml_text(te, f"{ns}Name") or _xml_text(te, "Name") or _xml_text(te, "name") or ""
        if not name.strip():
            continue

        uid = _xml_text(te, f"{ns}UID") or _xml_text(te, "UID") or _xml_text(te, "uid") or ""

        duration_str = _xml_text(te, f"{ns}Duration") or _xml_text(te, "Duration") or _xml_text(te, "duration") or "0"
        est = _parse_duration(duration_str)

        start_raw = (
            _xml_text(te, f"{ns}Start") or _xml_text(te, "Start")
            or _xml_text(te, "start") or None
        )
        end_raw = (
            _xml_text(te, f"{ns}Finish") or _xml_text(te, "Finish")
            or _xml_text(te, "finish") or _xml_text(te, f"{ns}End")
            or _xml_text(te, "End") or _xml_text(te, "end") or None
        )

        milestone_flag = _xml_text(te, f"{ns}Milestone") or _xml_text(te, "Milestone") or "0"
        
        # Hierarchy extraction
        summary_flag = _xml_text(te, f"{ns}Summary") or _xml_text(te, "Summary") or "0"
        outline_level = _xml_text(te, f"{ns}OutlineLevel") or _xml_text(te, "OutlineLevel") or "1"
        try:
            outline_level = int(float(outline_level))
        except:
            outline_level = 1

        # Extract PredecessorLink elements
        preds_data = []
        for pl in te.findall(f"{ns}PredecessorLink") or te.findall("PredecessorLink") or []:
            pred_uid = _xml_text(pl, f"{ns}PredecessorUID") or _xml_text(pl, "PredecessorUID") or ""
            if pred_uid:
                t_val = _xml_text(pl, f"{ns}Type") or _xml_text(pl, "Type") or "1"
                l_val = _xml_text(pl, f"{ns}LinkLag") or _xml_text(pl, "LinkLag") or "0"
                
                # 0=FF, 1=FS, 2=SF, 3=SS
                p_type = "FS"
                if t_val == "0": p_type = "FF"
                elif t_val == "1": p_type = "FS"
                elif t_val == "2": p_type = "SF"
                elif t_val == "3": p_type = "SS"
                
                # Lag is often in tenths of minutes
                lag_hours = 0.0
                try:
                    lag_hours = float(l_val) / 600.0
                except:
                    pass
                
                preds_data.append({
                    "uid": pred_uid,
                    "type": p_type,
                    "lag": lag_hours
                })

        tasks.append({
            "wbs_code": _xml_text(te, f"{ns}WBS") or _xml_text(te, "WBS") or None,
            "title": name.strip(),
            "description": (
                _xml_text(te, f"{ns}Notes") or _xml_text(te, "Notes")
                or _xml_text(te, "Description") or _xml_text(te, "description") or ""
            ),
            "estimated_hours": est,
            "priority": _norm_priority(_xml_text(te, f"{ns}Priority") or _xml_text(te, "Priority")),
            "status": "not_started",
            "task_type": "milestone" if milestone_flag == "1" else "task",
            "planned_start": _parse_date(start_raw),
            "planned_end": _parse_date(end_raw),
            "dependencies_raw": [],  # For name-based resolution (legacy)
            "xml_uid": uid,          # For UID-based resolution (preferred)
            "predecessor_links": preds_data, # List of {uid, type, lag}
            "is_summary": summary_flag == "1",
            "outline_level": outline_level,
        })

    return {"title": project_title, "tasks": tasks, "materials": []}


# ---------- Helpers ----------

def _safe_float(val: str) -> float:
    try:
        return float(val.replace(",", ""))
    except (ValueError, AttributeError):
        return 0.0


def _norm_priority(val: Optional[str]) -> str:
    if not val:
        return "Medium"
    v = val.lower().strip()
    mapping = {
        "low": "Low", "med": "Medium", "medium": "Medium", "high": "High",
        "critical": "Critical", "crit": "Critical", "hi": "High", "lo": "Low",
        "0": "Low", "100": "Low", "200": "Low", "300": "Medium", "500": "Medium",
        "600": "High", "700": "High", "800": "Critical", "900": "Critical", "1000": "Critical",
    }
    return mapping.get(v, "Medium")


def _norm_status(val: Optional[str]) -> str:
    if not val:
        return "not_started"
    v = val.lower().strip()
    mapping = {
        "not started": "not_started", "not_started": "not_started", "todo": "not_started",
        "in progress": "in_progress", "in_progress": "in_progress", "active": "in_progress",
        "completed": "completed", "done": "completed", "complete": "completed",
        "stalled": "stalled", "cancelled": "cancelled", "void": "cancelled",
    }
    return mapping.get(v, "not_started")


def _parse_date(val: Optional[str]) -> Optional[datetime]:
    """Parse a date string into a datetime object. Returns None on failure."""
    if not val:
        return None
    val = val.strip()
    # Strip timezone offset like +08:00
    cleaned = re.sub(r'[+-]\d{2}:\d{2}$', '', val)
    
    for v in (val, cleaned):
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%d-%b-%Y",
            "%d-%b-%y",
        ):
            try:
                return datetime.strptime(v, fmt)
            except ValueError:
                continue
    return None


def _parse_duration(val: str) -> float:
    """Parse ISO 8601 duration or simple hour values."""
    if not val:
        return 0.0
    if val.startswith("PT"):
        hours = 0.0
        h = re.search(r"(\d+)H", val)
        m = re.search(r"(\d+)M", val)
        if h:
            hours += float(h.group(1))
        if m:
            hours += float(m.group(1)) / 60
        return hours
    return _safe_float(val)


def _xml_text(el, tag: str) -> Optional[str]:
    child = el.find(tag)
    return child.text if child is not None and child.text else None


# ---------- Endpoint ----------

@router.post("/import", response_model=ProjectSchema)
async def import_project(
    file: UploadFile = File(...),
    project_title: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Import a project from CSV, JSON, or XML file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    raw = await file.read()

    # Try multiple encodings
    content = None
    for encoding in ("utf-8-sig", "utf-8", "gbk", "gb2312", "latin-1"):
        try:
            content = raw.decode(encoding)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if content is None:
        raise HTTPException(status_code=400, detail="Unable to decode file. Please use UTF-8 encoding.")

    try:
        if ext == "csv":
            parsed = _parse_csv(content)
        elif ext == "json":
            parsed = _parse_json(content)
        elif ext in ("xml", "mpp"):
            parsed = _parse_xml(content)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: .{ext}. Supported: .csv, .json, .xml"
            )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    if not parsed.get("tasks"):
        raise HTTPException(status_code=400, detail="No tasks found in the file. Please check the file format.")

    try:
        # Create project
        db_project = Project(
            title=project_title or parsed.get("title", "Imported Project"),
            description=parsed.get("description") or f"Imported from {file.filename}",
            industry=industry or parsed.get("industry", ""),
            summary=f"Imported from {file.filename} ({len(parsed.get('tasks', []))} tasks)",
            status="planning",
        )
        db.add(db_project)
        await db.flush()

        # Create tasks
        task_map_by_title = {}
        task_map_by_uid = {} # XML Only: uid -> db_task_id
        
        # Temporary storage for deferred resolution
        deferred_tasks = []

        for t_data in parsed.get("tasks", []):
            deps_raw = t_data.pop("dependencies_raw", [])
            xml_uid = t_data.pop("xml_uid", None)
            predecessor_uids = t_data.pop("predecessor_uids", [])
            
            db_task = Task(
                project_id=db_project.id,
                wbs_code=t_data.get("wbs_code"),
                title=t_data.get("title", "Untitled"),
                description=t_data.get("description", ""),
                original_duration=t_data.get("estimated_hours", 0), # Map to newer field
                priority=t_data.get("priority", "Medium"),
                status=t_data.get("status", "not_started"),
                task_type=t_data.get("task_type", "task"),
                planned_start=t_data.get("planned_start"),
                planned_end=t_data.get("planned_end"),
                responsible_party=t_data.get("responsible_party"),
                # Hierarchy
                is_summary=t_data.get("is_summary", False),
                outline_level=t_data.get("outline_level", 1),
            )
            db.add(db_task)
            await db.flush()
            
            task_info = {
                "id": db_task.id, 
                "db_task": db_task,
                "deps_raw": deps_raw,
                "predecessor_links": t_data.get("predecessor_links", [])
            }
            
            task_map_by_title[db_task.title] = task_info
            if xml_uid:
                task_map_by_uid[xml_uid] = task_info
            
            deferred_tasks.append(task_info)

        # Resolve dependencies
        for info in deferred_tasks:
            current_task_id = info["db_task"].id
            resolved_relationships = []
            
            # 1. Try UID based resolution (XML)
            if info.get("predecessor_links") and task_map_by_uid:
                for link in info["predecessor_links"]:
                    target = task_map_by_uid.get(link["uid"])
                    if target:
                        resolved_relationships.append({
                            "pred_id": target["id"], "type": link["type"], "lag": link["lag"]
                        })
            
            # 2. Key Name based resolution (CSV/JSON or fallback)
            elif info.get("deps_raw"):
                for dep_ref in info["deps_raw"]:
                    target = task_map_by_title.get(dep_ref)
                    if target:
                        resolved_relationships.append({
                            "pred_id": target["id"], "type": "FS", "lag": 0
                        })
            
            from app.models.project import TaskRelationship

            for rel in resolved_relationships:
                # Create TaskRelationship (Predecessor -> Successor)
                # Successor is current task. Predecessor is the target.
                tr = TaskRelationship(
                    project_id=db_project.id,
                    predecessor_id=rel["pred_id"],
                    successor_id=current_task_id,
                    type=rel["type"],
                    lag=rel["lag"]
                )
                db.add(tr)

        await db.commit()

    except Exception as e:
        await db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error while saving: {str(e)}")

    # Reload with relationships
    stmt = (
        select(Project)
        .where(Project.id == db_project.id)
        .options(
            selectinload(Project.tasks).selectinload(Task.materials),
            selectinload(Project.tasks).selectinload(Task.relationships_pred),
            selectinload(Project.risks),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one()
