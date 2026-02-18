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

---
*Use these guidelines to audit any schedule generated or imported into the AI PM Platform. A "Pass" on the DCMA 14-Point Assessment is required for high-stakes engineering projects.*
