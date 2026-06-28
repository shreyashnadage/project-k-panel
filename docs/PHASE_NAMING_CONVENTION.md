# Phase Naming Convention
## Descriptive Phase Names for Clarity

**Effective Date**: 28 June 2026  
**Updated By**: Suggestion Implementation  
**Status**: ACTIVE

---

## 🎯 The Rule

**Every phase MUST include a descriptive name, not just a number.**

### Format
```
PHASE_X: [Descriptive Name]

Examples:
✅ PHASE_0-1: Modular Dashboard Foundation
✅ PHASE_2: Financial Visualization & Advanced Charting
✅ PHASE_3: White-Label System & Multi-Tenant Configuration
✅ PHASE_4: Real-Time Updates & Production Hardening
✅ PHASE_5: Windows Service & Fleet Monitoring

❌ PHASE_0-1 (too vague)
❌ Phase 2 (missing number prefix)
❌ PHASE_2_Advanced_Charting (wrong format)
```

---

## 📋 Complete Phase List with Descriptions

| Phase | Name | Duration | Goal | Team Size |
|-------|------|----------|------|-----------|
| **PHASE_0-1** | Modular Dashboard Foundation | 2-3 weeks | Widget system + 3 core widgets | 2 FE + 1 BE |
| **PHASE_2** | Financial Visualization & Advanced Charting | 2-3 weeks | 5+ financial widgets + Superset | 1 FE |
| **PHASE_3** | White-Label System & Multi-Tenant Configuration | 2 weeks | Tenant branding + feature flags | 1 FE + 1 BE |
| **PHASE_4** | Real-Time Updates & Production Hardening | 1-2 weeks | WebSocket + ELK logging + optimization | 1 FE + 1 BE |
| **PHASE_5** | Windows Service & Fleet Monitoring | 2 weeks | Agent service + monitoring dashboard | 1 FE + 1 BE |

---

## 📁 Directory Naming

### Directories Must Use Full Description

```
docs/phases/

✅ GOOD:
  ├── PHASE_0-1_Modular_Dashboard_Foundation/
  ├── PHASE_2_Financial_Visualization/
  ├── PHASE_3_White_Label_System/
  ├── PHASE_4_Real_Time_Updates/
  └── PHASE_5_Windows_Service/

❌ BAD:
  ├── PHASE_0-1/
  ├── PHASE_2/
  ├── phase_3/
  └── Phase_4_realtime/
```

---

## 📝 Document Naming

### Files Must Include Phase Description in Header

**File Name Format**: `PHASE_X_[Description]_DOCUMENT_TYPE.md`

```
✅ GOOD:
  PHASE_0-1_Modular_Dashboard_Foundation_PLAN.md
  PHASE_0-1_Modular_Dashboard_Foundation_IMPLEMENTATION.md
  PHASE_2_Financial_Visualization_TESTING.md
  PHASE_3_White_Label_System_USAGE_GUIDE.md

❌ BAD:
  PHASE_0-1_PLAN.md (missing description)
  Phase_1_Plan.md (wrong format)
  PLAN_PHASE_0-1.md (wrong order)
```

---

## 📖 Document Header Format (Updated)

Every document MUST start with this header including the description:

```markdown
# Phase X: [Descriptive Name] — [Document Type]

**Document Type**: [Plan/Implementation/Testing/Usage Guide/Completion]  
**Phase**: X: [Descriptive Name] (Weeks N-M)  
**Owner**: [Name] ([Role])  
**Status**: [In Progress / Complete / Blocked]  
**Last Updated**: YYYY-MM-DD  
**Git Commit**: [hash]

---

## Executive Summary
[2-3 sentence overview of what this phase delivers]

---
```

### Example Header
```markdown
# Phase 0-1: Modular Dashboard Foundation — Plan

**Document Type**: Plan  
**Phase**: 0-1: Modular Dashboard Foundation (Weeks 1-3)  
**Owner**: Frontend Lead  
**Status**: In Progress  
**Last Updated**: 2026-06-28  
**Git Commit**: 8601c5c

---

## Executive Summary

Phase 0-1 builds the foundation for a modular fintech dashboard by implementing a widget registry system, creating 3 core financial widgets (KPI, Chart, Table), and integrating with the CloudPlatform API. By week 3, we'll have a pilot-ready dashboard ready for 5-10 MSME partners.
```

---

## 🔄 Git Commits Must Include Description

### Commit Message Format

```bash
[TYPE] phase-X: [Description] - Brief change description

Examples:
✅ [feat] phase-0-1: Modular Dashboard Foundation - Add KPI widget
✅ [test] phase-0-1: Modular Dashboard Foundation - Add 45 test cases
✅ [docs] phase-0-1: Modular Dashboard Foundation - Update README
✅ [feat] phase-2: Financial Visualization - Implement waterfall chart

❌ [feat] phase-0-1: Add KPI widget (missing description)
❌ [feat] Add widget (too vague)
```

---

## 📊 README Update Format

### README Must Show Full Phase Names

```markdown
## Phase Status

| Phase | Name | Status | Duration | Docs |
|-------|------|--------|----------|------|
| **0-1** | Modular Dashboard Foundation | ✅ COMPLETE | W1-3 | [Link](phases/) |
| **2** | Financial Visualization & Advanced Charting | 🚀 READY | W4-6 | [Link](phases/) |
| **3** | White-Label System & Multi-Tenant Configuration | ⏳ PLANNED | W7-8 | [Link](phases/) |
| **4** | Real-Time Updates & Production Hardening | ⏳ PLANNED | W9-10 | [Link](phases/) |
| **5** | Windows Service & Fleet Monitoring | ⏳ PLANNED | W11+ | [Link](phases/) |

---

## PHASE_0-1: Modular Dashboard Foundation

**Timeline**: Week 1-3 | **Status**: In Progress | **[Full Details](phases/PHASE_0-1_Modular_Dashboard_Foundation/)**

### What We're Building
- Widget registry system
- 3 core financial widgets (KPI, Chart, Table)
- Dark-first design
- Real API integration
```

---

## 🎯 Weekly Progress Report Format

**File Name**: `WEEKLY_PROGRESS_WEEK_N.md`

**Header**:
```markdown
# Phase X: [Description] — Week N Progress Report

**Week of**: [Date Range]  
**Phase**: X: [Descriptive Name]  
**Status**: 🟢 On Track / 🟡 At Risk / 🔴 Blocked
```

---

## ✅ Checklist: Phase Naming Consistency

Before starting a phase, verify:

- [ ] Phase has a descriptive name (not just a number)
- [ ] Directory uses full name: `PHASE_X_Description/`
- [ ] All document files include description in header
- [ ] First document header includes full description
- [ ] Commit messages include phase description
- [ ] README shows full phase names in table
- [ ] Weekly progress reports reference full name
- [ ] Completion report uses full description

**RULE**: Missing any of these = Naming incomplete. Fix before proceeding.

---

## 📋 All Phase Names (Reference)

```
PHASE_0-1: Modular Dashboard Foundation
├─ Weeks: 1-3
├─ Goal: Build widget registry + 3 core widgets
├─ Team: 2 FE + 1 BE
└─ Success: Pilot-ready dashboard with tests

PHASE_2: Financial Visualization & Advanced Charting
├─ Weeks: 4-6
├─ Goal: 5+ financial widgets + Apache Superset
├─ Team: 1 FE
└─ Success: Enterprise-grade financial dashboards

PHASE_3: White-Label System & Multi-Tenant Configuration
├─ Weeks: 7-8
├─ Goal: Tenant branding + feature flags + Clerk
├─ Team: 1 FE + 1 BE
└─ Success: Ready for 5+ white-label partners

PHASE_4: Real-Time Updates & Production Hardening
├─ Weeks: 9-10
├─ Goal: WebSocket integration + ELK logging + optimization
├─ Team: 1 FE + 1 BE
└─ Success: Production-ready with Lighthouse 90+

PHASE_5: Windows Service & Fleet Monitoring
├─ Weeks: 11+
├─ Goal: Agent Windows service + fleet dashboard
├─ Team: 1 FE + 1 BE
└─ Success: Ready for pilot deployment to MSMEs
```

---

## 🚀 Implementation Examples

### Example 1: Starting Phase 0-1

```bash
# Create directory with FULL NAME
mkdir -p docs/phases/PHASE_0-1_Modular_Dashboard_Foundation

# Create files with FULL DESCRIPTION
touch docs/phases/PHASE_0-1_Modular_Dashboard_Foundation/PHASE_0-1_Modular_Dashboard_Foundation_PLAN.md
touch docs/phases/PHASE_0-1_Modular_Dashboard_Foundation/PHASE_0-1_Modular_Dashboard_Foundation_IMPLEMENTATION.md

# Commit with FULL DESCRIPTION
git commit -m "[docs] phase-0-1: Modular Dashboard Foundation - Initialize phase"
```

### Example 2: File Header

```markdown
# Phase 0-1: Modular Dashboard Foundation — Plan

**Document Type**: Plan  
**Phase**: 0-1: Modular Dashboard Foundation (Weeks 1-3)  
**Owner**: Frontend Lead  
**Status**: In Progress  
**Last Updated**: 2026-06-28

---

## Executive Summary

Phase 0-1 builds the foundation for a modular fintech dashboard...
```

### Example 3: README Entry

```markdown
## PHASE_0-1: Modular Dashboard Foundation

**Timeline**: Week 1-3 | **Status**: In Progress | **Details**: [Link](phases/PHASE_0-1_Modular_Dashboard_Foundation/)

### What We're Building
- Widget registry system
- 3 core financial widgets
- Dark-first design with Tailwind CSS
- Real API integration

### Expected Outcomes
- ✅ Modular widget system working
- ✅ Lighthouse score 85+
- ✅ WCAG 2.1 AA compliant
- ✅ Ready for Phase 2
```

---

## 📝 Updated TEAM_QUICK_REFERENCE Card

**Print this updated version:**

```
PHASE NAMING RULE:
Every phase MUST have a descriptive name!

✅ PHASE_0-1: Modular Dashboard Foundation
✅ PHASE_2: Financial Visualization & Advanced Charting
✅ PHASE_3: White-Label System & Multi-Tenant Configuration
✅ PHASE_4: Real-Time Updates & Production Hardening
✅ PHASE_5: Windows Service & Fleet Monitoring

❌ PHASE_0-1 (too vague)
❌ Phase 2 (wrong format)

Use full names in:
- Directory names
- File names
- Document headers
- Commit messages
- README entries
- Weekly progress reports
```

---

## ✨ Benefits of Descriptive Phase Names

1. **Clarity**: Everyone instantly knows what each phase does
2. **Communication**: Easier to discuss "Financial Visualization phase" vs "Phase 2"
3. **Documentation**: Clear phase description in every document
4. **Search**: Easier to find phase-related files and discussions
5. **Professionalism**: Looks more organized and intentional
6. **Scalability**: Works with 5 phases or 50 phases

---

## 🎯 Implementation Checklist

Before using new naming convention:

- [ ] Update PROJECT_GOVERNANCE.md with full phase names
- [ ] Update TEAM_QUICK_REFERENCE.md with examples
- [ ] Update PHASE_TEMPLATE_PACK.md with new format
- [ ] Create new directory: `PHASE_0-1_Modular_Dashboard_Foundation/`
- [ ] Use full names in all document headers
- [ ] Use full names in all commit messages
- [ ] Update README.md with full phase descriptions
- [ ] Communicate new naming convention to team

---

## Final Rule

**From now on, all phases MUST use descriptive names:**

```
PHASE_X: [Descriptive Name]
```

No exceptions. No shortcuts. Make it clear what each phase delivers.

---

**Effective**: 28 June 2026  
**Status**: ACTIVE - Update all existing docs and use for all future phases  
**Questions?** See PROJECT_GOVERNANCE.md or create an issue

---

**Example Full Phase Name List** (for reference):

- ✅ PHASE_0-1: Modular Dashboard Foundation
- ✅ PHASE_2: Financial Visualization & Advanced Charting
- ✅ PHASE_3: White-Label System & Multi-Tenant Configuration
- ✅ PHASE_4: Real-Time Updates & Production Hardening
- ✅ PHASE_5: Windows Service & Fleet Monitoring

Use this naming convention **consistently across all documentation**.
