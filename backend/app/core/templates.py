
# Standard Engineering Templates

ENGINEERING_TEMPLATES = {
    "BOQ": [
        {"category": "Civil", "item": "Excavation", "unit": "m3", "description": "Bulk excavation for foundation"},
        {"category": "Civil", "item": "Backfill", "unit": "m3", "description": "Compacted backfill"},
        {"category": "Concrete", "item": "Lean Concrete", "unit": "m3", "description": "C15 blinding concrete"},
        {"category": "Concrete", "item": "Structural Concrete", "unit": "m3", "description": "C30 reinforced concrete"},
        {"category": "Structural", "item": "Steel Beam", "unit": "ton", "description": "I-Beam fabrication and erection"},
        {"category": "Piping", "item": "CS Pipe 4 inch", "unit": "m", "description": "Carbon Steel Pipe Sch 40"}
    ],
    "VDR_Rotating": [
        {"code": "VDR-001", "title": "General Arrangement Drawing", "stage": "Design"},
        {"code": "VDR-002", "title": "P&ID", "stage": "Design"},
        {"code": "VDR-003", "title": "Foundation Loads", "stage": "Design"},
        {"code": "VDR-004", "title": "Electrical Load List", "stage": "Design"},
        {"code": "VDR-005", "title": "Motor Datasheet", "stage": "Procurement"},
        {"code": "VDR-006", "title": "Performance Curve", "stage": "Procurement"},
        {"code": "VDR-007", "title": "Noise Level Validation", "stage": "Testing"},
        {"code": "VDR-008", "title": "Spare Parts List", "stage": "Commissioning"},
        {"code": "VDR-009", "title": "Installation Manual", "stage": "Construction"}
    ],
    "VDR_Vessel": [
        {"code": "VDR-V01", "title": "General Arrangement & Nozzle Orientation", "stage": "Design"},
        {"code": "VDR-V02", "title": "Design Calculation Report (PV Elite/Compress)", "stage": "Design"},
        {"code": "VDR-V03", "title": "Material Certificates", "stage": "Procurement"},
        {"code": "VDR-V04", "title": "WPS/PQR (Welding Procedures)", "stage": "Construction"},
        {"code": "VDR-V05", "title": "NDT Plan & Reports", "stage": "Testing"},
        {"code": "VDR-V06", "title": "Hydrotest Procedure", "stage": "Testing"},
        {"code": "VDR-V07", "title": "Surface Preparation & Painting Procedure", "stage": "Construction"},
        {"code": "VDR-V08", "title": "Nameplate Drawing", "stage": "Construction"}
    ],
    "ITP": [
        {"activity": "Material Receipt", "check": "Visual Inspection & MTC Review", "acceptance_criteria": "No damage, MTC complies with spec", "verifier": "QC Inspector"},
        {"activity": "Fit-up", "check": "Dimension & Alignment", "acceptance_criteria": "Tolerance +/- 1mm", "verifier": "Welding Inspector"},
        {"activity": "Welding", "check": "Process parameters (Amps, Volts)", "acceptance_criteria": "WPS compliance", "verifier": "Welding Inspector"},
        {"activity": "NDT", "check": "RT/UT/MT/PT", "acceptance_criteria": "ASME Sec VIII / B31.3", "verifier": "NDT Level II"},
        {"activity": "Hydrotest", "check": "Pressure & Holding Time", "acceptance_criteria": "No leakage, pressure stable", "verifier": "Client/TPI"},
        {"activity": "Painting", "check": "DFT Measurement", "acceptance_criteria": "DFT within spec range", "verifier": "Painting Inspector"},
        {"activity": "Final Inspection", "check": "Completeness & Workmanship", "acceptance_criteria": "Ready for shipment", "verifier": "Project Manager"}
    ]
}
