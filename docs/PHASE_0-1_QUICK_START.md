# Phase 0-1: Quick Start Implementation Guide

**Start Date**: 28 June 2026  
**Duration**: 3 weeks  
**Goal**: Modular dashboard foundation ready for pilot

---

## ⚡ Day 1-2: Setup (Estimated 8 hours)

### Step 1: Clone Repository
```bash
git clone https://github.com/shreyashnadage/project-k-panel.git
cd project-k-panel
git checkout -b phase/0-1
```

### Step 2: Install Dependencies
```bash
npm install
```

### Step 3: Create .env.local
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_TENANT_ID=default-tenant
```

### Step 4: Start Dev Server
```bash
npm run dev
# Dashboard should be at http://localhost:3000
```

### Step 5: Verify Everything Works
- [ ] Dev server runs without errors
- [ ] No TypeScript errors
- [ ] ESLint passes
- [ ] Dashboard loads at http://localhost:3000

**Milestone: Foundation ready ✅**

---

## 📦 Day 3-4: Widget Registry (Estimated 12 hours)

### Create Widget Type System
```bash
# Create file: src/types/widgets.ts
```

See template in `/docs/PHASE_TEMPLATE_PACK.md` for code structure.

### Create Widget Registry
```bash
# Create file: src/lib/widgetRegistry.ts
```

This file defines:
- `WIDGET_DEFINITIONS` (all available widgets)
- `DEFAULT_LAYOUTS` (per-role widget assignments)
- `WidgetManager` class (get/save/update layouts)

### Create API Client
```bash
# Create file: src/lib/api.ts
```

Endpoints needed:
- `GET /api/dashboard/kpis?tenant_id=...`
- `GET /api/dashboard/vouchers?tenant_id=...&skip=0&limit=50`
- `GET /api/dashboard/cash-flow?tenant_id=...`

### Setup State Management
```bash
# Create file: src/lib/store.ts (Zustand)
# Create file: src/lib/queryClient.ts (React Query)
```

**Milestone: Architecture ready ✅**

---

## 🎨 Day 5-9: Build 3 Widgets (Estimated 20 hours)

### Widget 1: KPI Widget (Days 5-6)

```bash
# Create: src/components/widgets/KPIWidget.tsx
```

Displays:
- Total ledgers
- Total vouchers
- Last sync time
- Sync health (green/yellow/red indicator)

**Requirements**:
- Fetch data from `GET /api/dashboard/kpis`
- Format numbers with commas
- Handle loading state (skeleton)
- Handle error state

**Test**: Unit tests with 90%+ coverage

---

### Widget 2: Cash Flow Chart (Days 7-8)

```bash
# Create: src/components/widgets/CashFlowChartWidget.tsx
# Install: npm install recharts
```

Displays:
- 30-day area chart
- Inflow/outflow amounts
- Interactive tooltip

**Requirements**:
- Fetch data from `GET /api/dashboard/cash-flow`
- Use Recharts ResponsiveContainer
- Format Y-axis with ₹ currency symbol
- Dark theme (slate-950 + teal-500)

**Test**: Unit tests with 90%+ coverage

---

### Widget 3: Vouchers Table (Days 9-10)

```bash
# Create: src/components/widgets/VouchersTableWidget.tsx
# Install: npm install @tanstack/react-table (already in deps)
```

Displays:
- Date, Voucher#, Party, Type, Amount columns
- 50 rows per page
- Pagination buttons
- Color-coded transaction types

**Requirements**:
- Fetch from `GET /api/dashboard/vouchers?skip=X&limit=50`
- Format currency: `₹23,45,000.50`
- Devanagari text support (test with Hindi names)
- Responsive grid layout

**Test**: Unit tests with 90%+ coverage

---

## 🧪 Day 10-14: Testing (Estimated 15 hours)

### Unit Tests
```bash
npm run test:unit
```
- Target: 80%+ code coverage
- Each widget: 5-8 test cases
- Test loading, error, data display states

### Integration Tests
```bash
npm run test:integration
```
- Test API endpoints
- Test data flow from API → component
- Test pagination & filtering

### Manual Testing Checklist
```
Dashboard Loading:
  ☐ No console errors
  ☐ Loads in < 2 seconds
  ☐ All widgets render

KPI Widget:
  ☐ Shows correct numbers
  ☐ Health indicator visible
  ☐ Last sync date formatted
  
Chart Widget:
  ☐ Area chart renders
  ☐ Tooltip works on hover
  ☐ Responsive to window size
  
Table Widget:
  ☐ Shows 50 rows per page
  ☐ Pagination buttons work
  ☐ Currency formatted ₹
  ☐ Hindi text displays correctly

Performance:
  ☐ Lighthouse score 85+
  ☐ First paint < 2s
  ☐ No memory leaks

Accessibility:
  ☐ Keyboard navigation works
  ☐ Tab order is logical
  ☐ Color contrast 4.5:1+
  ☐ Screen reader friendly

Browsers:
  ☐ Chrome latest
  ☐ Firefox latest
  ☐ Safari latest
  ☐ Edge latest
```

**Milestone: All tests passing ✅**

---

## 📚 Day 15: Documentation & Release (Estimated 6 hours)

### Create 4 Remaining Docs
```bash
# Create: docs/phases/PHASE_0-1_Modular_Dashboard_Foundation/IMPLEMENTATION.md
# Create: docs/phases/PHASE_0-1_Modular_Dashboard_Foundation/TESTING.md
# Create: docs/phases/PHASE_0-1_Modular_Dashboard_Foundation/USAGE.md
# Create: docs/phases/PHASE_0-1_Modular_Dashboard_Foundation/COMPLETION.md
```

See templates in `/docs/PHASE_TEMPLATE_PACK.md`

### Get Sign-Offs
- [ ] PM: Feature review + approval
- [ ] Eng Lead: Code quality review + approval
- [ ] QA: Testing verification + approval

### Release
```bash
# Create version tag
git tag -a v0.1.0 -m "Phase 0-1: Modular Dashboard Foundation"

# Push everything
git push origin phase/0-1
git push origin staging
git push origin --tags

# Update README
# - Add Phase 0-1 status: ✅ COMPLETE
# - Add metrics (coverage, lighthouse, etc)
# - Add links to phase docs
```

**Milestone: Phase released ✅**

---

## 🔄 Git Workflow (Day by Day)

### Every Day
```bash
# Commit your work (good messages!)
git commit -m "[feat] phase-0-1: Add KPI widget with API integration"

# Push to remote
git push origin phase/0-1
```

### By End of Week
```bash
# Update phase documentation
git commit -m "[docs] phase-0-1: Update progress"
git push origin phase/0-1
```

### When Phase Complete
```bash
# Create all 4 remaining docs
git add docs/phases/PHASE_0-1_Modular_Dashboard_Foundation/
git commit -m "[docs] phase-0-1: Add IMPLEMENTATION, TESTING, USAGE, COMPLETION"

# Update main README
git commit -m "[docs] update README (Phase 0-1 complete)"

# Push and tag
git push origin phase/0-1
git push origin staging
git tag -a v0.1.0 -m "Phase 0-1 Complete"
git push origin --tags
```

---

## 🎯 Success Criteria Checklist

By end of Phase 0-1, verify:

### Code ✅
- [ ] Widget registry system works
- [ ] All 3 widgets render without errors
- [ ] ESLint: 0 errors
- [ ] TypeScript strict: 0 errors
- [ ] No console errors in prod build

### Testing ✅
- [ ] 80%+ unit test coverage
- [ ] All integration tests pass
- [ ] Lighthouse 85+
- [ ] WCAG 2.1 AA compliant
- [ ] Tested on 4 major browsers

### Documentation ✅
- [ ] PLAN.md ✅ (already created)
- [ ] IMPLEMENTATION.md created
- [ ] TESTING.md created
- [ ] USAGE.md created
- [ ] COMPLETION.md created with sign-offs
- [ ] README.md updated

### Release ✅
- [ ] v0.1.0 tag created
- [ ] Pushed to remote
- [ ] 3 approvals obtained

---

## 📦 File Structure (What You'll Create)

```
src/
├── types/
│   └── widgets.ts                    ← Widget types
├── lib/
│   ├── widgetRegistry.ts             ← Widget definitions & layouts
│   ├── queryClient.ts                ← React Query setup
│   ├── store.ts                      ← Zustand state
│   └── api.ts                        ← API client
├── components/
│   ├── Dashboard.tsx                 ← Main component
│   ├── WidgetContainer.tsx           ← Widget wrapper
│   └── widgets/
│       ├── KPIWidget.tsx             ← KPI display
│       ├── CashFlowChartWidget.tsx   ← Chart display
│       └── VouchersTableWidget.tsx   ← Table display
└── pages/
    └── index.tsx                     ← Route: /

docs/phases/PHASE_0-1_Modular_Dashboard_Foundation/
├── PLAN.md                           ✅ (created)
├── IMPLEMENTATION.md                 (create Day 15)
├── TESTING.md                        (create Day 15)
├── USAGE.md                          (create Day 15)
└── COMPLETION.md                     (create Day 15)
```

---

## 🚀 Ready to Start?

**Before Day 1**:
1. Read `/docs/GOVERNANCE_LIGHTWEIGHT.md` (10 min)
2. Read `/docs/phases/PHASE_0-1_Modular_Dashboard_Foundation/PLAN.md` (15 min)
3. Clone repository and run `npm install`
4. Verify dev server starts at http://localhost:3000

**Day 1**: Start implementation!

---

## 💡 Pro Tips

### Commit Often
- Commit after each widget is done
- Commit after each test suite passes
- Push daily (even if incomplete)

### Test Early
- Write tests as you build, not after
- Verify Lighthouse score by Day 12
- Don't wait until Day 15 to test

### Document As You Go
- Note decisions & issues in a scratch file
- Use those notes when writing IMPLEMENTATION.md on Day 15
- Makes documentation super fast

### API First
- Verify API endpoints are working before building widgets
- Mock data if API not ready (use json-server or MSW)
- Test with real data by Day 9

---

## ❓ Questions?

- **Setup issues?** → See `/docs/guides/DEVELOPER_SETUP.md`
- **Widget help?** → See `/docs/guides/WIDGET_DEVELOPMENT_GUIDE.md`
- **Governance?** → See `/docs/GOVERNANCE_LIGHTWEIGHT.md`
- **Tech help?** → See `/docs/guides/TROUBLESHOOTING.md`

---

**Start Date**: 28 June 2026  
**Target Completion**: 19 July 2026  
**Status**: Ready to begin! 🚀

Good luck! Ship it! 🎉
