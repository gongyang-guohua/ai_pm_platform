---
name: p6_scheduling_guidelines
description: Industry-standard project scheduling principles inspired by Oracle Primavera P6 and the DCMA 14-Point Assessment.
---

# Oracle P6 Scheduling Guidelines & "编制导则"

This skill provides a set of rigorous guidelines for creating, maintaining, and auditing project schedules within the AI PM Platform. These principles ensure technical integrity, logical consistency, and realistic project forecasting.

## 1. Network Logic & Topology
- **Closed Loop Requirement**: Every activity (except Project Start and Finish) must have at least one **predecessor** and one **successor**.
- **Dangling Logic**: Avoid "Open Ends." A task without a successor artificially creates float and hides the true critical path.
- **Logic Integrity Check**: Missing logic should be present in less than 5% of all activities.

## 2. Relationship Management
- **Primary Type**: **Finish-to-Start (FS)** is the preferred relationship type (target: >90% of all links).
- **Lags & Leads**:
    - **Leads (Negative Lags)**: Prohibited. Use overlapping logic (SS/FF) instead.
    - **Lags (Positive)**: Minimize usage. If a lag represents a distinct process (e.g., "Concrete Curing"), create a dedicated task. Lags should affect <5% of relationships.

## 3. Work Breakdown Structure (WBS)
- **Hierarchical Integrity**: Activities must be mapped to a WBS node.
- **Level of Effort (LOE)**: Used for management/support tasks that span the duration of other tasks. They do not drive the critical path.

## 4. Activity Constraints
- **Soft Constraints**: Prefer "Start No Earlier Than" for external dependencies.
- **Hard Constraints**: Avoid "Must Finish On" or "Mandatory Start/Finish" as they override mathematical logic. Limit to <5% of activities.
- **Negative Float**: Hard constraints often cause negative float, signaling a broken plan that requires immediate mitigation.

## 5. Duration & Granularity
- **Task Length**: Aim for durations between 10 and 20 working days.
- **High Duration Tasks**: Avoid tasks longer than 44 days (2 months) as they lack the granularity for effective tracking.

## 6. Float & Critical Path
- **Total Float (TF)**: Monitor for "High Float" (>44 days), which usually indicates missing logic.
- **Critical Path Length Index (CPLI)**: A value <1.0 indicates the project is at risk of missing its finish date.

## 7. Baseline Management
- **Snapshot Requirement**: Save a "Baseline" before project execution.
- **Variance Analysis**: Compare current dates vs. baseline dates (BL Start, BL Finish) to calculate Schedule Variance (SV).


## 8. P6 Functional Requirements for AI PM Platform
To achieve industry-standard capabilities comparable to Oracle Primavera P6, the platform must implement the following core modules:

### 8.1 Core Scheduling Engine (CPM Engine)
Strict adherence to contractually required scheduling algorithms.
- **Critical Path Method (CPM)**:
    - Support forward/backward pass calculations based on graph theory.
    - Accurately identify Critical Paths and Sub-critical Paths.
    - *Advanced*: Support Multiple Float Paths calculation to identify risks on non-critical paths.
- **Logic Relationships & Delays**:
    - Support FS (Finish-to-Start), SS (Start-to-Start), FF (Finish-to-Finish), SF (Start-to-Finish).
    - Support Lag (positive delay) and Lead (negative delay) for all relationship types.
    - *Use Case*: Concrete curing (Lag) or overlapping phases (SS+Lag).
- **Constraint Management**:
    - Support "Hard Constraints" (Must Finish By, Mandatory Start/Finish) for contractual milestones.
    - Support "Soft Constraints" (Start No Earlier Than, Finish No Later Than).

### 8.2 Resource & Cost Control
Granular management of Labor, Material, and Equipment (LME).
- **Resource Leveling**:
    - Priority-based automatic leveling to resolve peak resource conflicts (e.g., limited tower cranes).
    - Ability to shift non-critical tasks to smooth resource usage.
- **Resource Curves**:
    - Support non-linear distributions (Bell curve, S-curve) to model realistic work performance (slow start -> peak -> ramp down).
- **S-Curves & Histograms**:
    - Generate Cumulative Progress S-Curves and Resource Histograms via "Resource Usage Profiles".
    - Comparison of Planned vs. Actual value for progress payments.

### 8.3 Monitoring & Reporting
System for daily site management and executive reporting.
- **Look-ahead Schedule**:
    - Auto-generate "3-Week Rolling" or "Monthly Rolling" plans for site coordination.
- **Baseline Management**:
    - Support unlimited baseline versions (Tender, Contract, Monthly Updates).
    - Variance Analysis: Real-time comparison of Current vs. Baseline (Start/Finish variances).
- **Earned Value Management (EVM)**:
    - Built-in EVM metrics: PV, EV, AC, SPI, CPI.
    - Forecasting: Estimate to Complete (ETC) and Estimate at Completion (EAC) to warn of overruns.

### 8.4 Claims & Delay Analysis (Construction Specific)
Tools for Extension of Time (EOT) claims.
- **Analysis Techniques**:
    - Support "Time Impact Analysis" (TIA) and "As-Planned vs. As-Built".
- **Fragnet Insertion**:
    - Ability to insert a "Fragnet" (fragmentary network) representing a delay event into the schedule to quantify its impact on the completion date.

### 8.5 Enterprise Architecture & Integration
Scalability for multi-project groups.
- **Enterprise Project Structure (EPS)**:
    - Hierarchical management (Region -> Division -> Asset) for project grouping and roll-up.
- **Ecosystem Integration**:
    - **BIM**: 4D/5D simulation via Revit/Navisworks integration.
    - **Cost/Contract**: Integration with systems like Unifier for Cash Flow vs. Schedule.
    - **Lean Construction**: Support for Last Planner System (LPS).

---
*Use these guidelines to audit any schedule generated or imported into the AI PM Platform. A "Pass" on the DCMA 14-Point Assessment is required for high-stakes engineering projects.*
