# Phase 0-1: Modular Dashboard Foundation — Plan

**Timeline**: Weeks 1-3 (3 weeks)  
**Owner**: Frontend Lead  
**Status**: In Progress (Ready to Start)  
**Start Date**: 28 June 2026  
**End Date**: 19 July 2026 (estimate)

---

## Executive Summary

Phase 0-1 builds the foundation for a modular fintech dashboard. We'll implement a widget registry system, create 3 core financial widgets (KPI, Chart, Table), and integrate with the CloudPlatform API. By week 3, we'll have a pilot-ready dashboard for 5-10 MSME partners.

---

## What We're Building

### 1. Widget Registry System
- **Purpose**: Enable plug-and-play widget architecture
- **Deliverable**: `src/lib/widgetRegistry.ts`
- **Features**:
  - Define widgets once, use everywhere
  - Per-role default layouts (admin/finance/accountant/viewer)
  - Widget visibility toggling
  - Save user preferences to localStorage

### 2. KPI Widget
- **Purpose**: Show key metrics (total records, last sync, health)
- **Deliverable**: `src/components/widgets/KPIWidget.tsx`
- **Displays**:
  - Total ledgers synced
  - Total vouchers synced
  - Last sync timestamp
  - Sync health status (green/yellow/red)

### 3. Cash Flow Chart Widget
- **Purpose**: Show 30-day cash flow trend
- **Deliverable**: `src/components/widgets/CashFlowChartWidget.tsx`
- **Uses**: Recharts area chart
- **Data**: 30 days of inflow/outflow data

### 4. Vouchers Table Widget
- **Purpose**: Browse recent transactions
- **Deliverable**: `src/components/widgets/VouchersTableWidget.tsx`
- **Features**:
  - Display 100K+ vouchers efficiently
  - Pagination (50 per page)
  - Sorting by date, party, amount
  - Currency formatting (₹ with Indian locale)
  - Transaction type color coding

### 5. Dashboard Container
- **Purpose**: Orchestrate all widgets
- **Deliverable**: `src/components/Dashboard.tsx`
- **Features**:
  - Load widgets from registry
  - Apply role-based layouts
  - Fetch data via React Query
  - Dark-first design (slate-950 + teal-500)

### 6. API Integration
- **Purpose**: Connect to CloudPlatform API
- **Deliverables**:
  - `GET /api/dashboard/kpis` - fetch KPI data
  - `GET /api/dashboard/vouchers` - fetch paginated vouchers
  - `GET /api/dashboard/cash-flow` - fetch cash flow trend
  - `GET /api/tenants/{id}/config` - fetch tenant config
- **Backend**: FastAPI endpoints (to be implemented alongside)

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | Next.js 16 + React 19 + TypeScript | SSR, modern React, type safety |
| Styling | Tailwind CSS v4 | Dark-first, utilities, no bloat |
| State | React Query + Zustand | Server state + client state separation |
| Charts | Recharts | React-native, small bundle, perfect for KPIs |
| Tables | Custom with shadcn/ui | Full control, responsive, clean |
| Icons | lucide-react | Modern, consistent, dark-first support |
| Forms | React Hook Form + Zod | Lightweight, performant, TypeScript |

---

## Success Criteria

### Code Quality ✅
- [ ] ESLint: 0 errors
- [ ] TypeScript: strict mode, 0 errors
- [ ] No console errors in production build
- [ ] Code reviewed & approved

### Testing ✅
- [ ] Unit tests: 80%+ coverage
- [ ] All tests passing
- [ ] No memory leaks
- [ ] Cross-browser tested (Chrome, Firefox, Safari, Edge)

### Performance ✅
- [ ] Lighthouse score: 85+
- [ ] First Contentful Paint: < 2 seconds
- [ ] Load time from API: < 1 second
- [ ] Bundle size: < 150KB gzipped

### Accessibility ✅
- [ ] WCAG 2.1 AA compliant
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Color contrast: 4.5:1+

### Features ✅
- [ ] KPI widget displays real data
- [ ] Chart renders without errors
- [ ] Table shows vouchers with pagination
- [ ] Dark mode looks professional
- [ ] Responsive on desktop/tablet/mobile

---

## Timeline & Milestones

### Week 1: Setup & Foundation (Days 1-5)
**Goal**: Development environment ready, architecture in place

- **Day 1-2**: 
  - [ ] Next.js 16 project setup
  - [ ] Tailwind CSS v4 configured
  - [ ] shadcn/ui integrated
  - [ ] Git branch created

- **Day 3-4**:
  - [ ] React Query setup
  - [ ] Zustand store created
  - [ ] API client configured
  - [ ] Widget registry architecture designed

- **Day 5**:
  - [ ] Dashboard component skeleton
  - [ ] Environment variables set up
  - [ ] Dev server running locally
  - [ ] **Milestone: Foundation ready ✅**

### Week 2: Widget Implementation (Days 6-10)
**Goal**: All 3 widgets rendering with real data

- **Day 6-7**:
  - [ ] KPI widget component created
  - [ ] Fetch KPI data via API
  - [ ] Format currency (₹) correctly
  - [ ] Unit tests for KPI widget

- **Day 8-9**:
  - [ ] Chart widget component created
  - [ ] Recharts area chart integrated
  - [ ] Fetch cash flow data via API
  - [ ] Unit tests for chart widget

- **Day 10**:
  - [ ] Table widget component created
  - [ ] Pagination working (50 per page)
  - [ ] Currency formatting applied
  - [ ] Unit tests for table widget
  - [ ] **Milestone: All widgets rendering ✅**

### Week 3: Testing & Documentation (Days 11-15)
**Goal**: Production-ready, fully tested, signed off

- **Day 11-12**:
  - [ ] Integration tests (API + widgets)
  - [ ] E2E tests (critical paths)
  - [ ] Performance testing (Lighthouse)
  - [ ] Accessibility audit (WCAG)

- **Day 13-14**:
  - [ ] Bug fixes from testing
  - [ ] Code coverage 80%+ verification
  - [ ] Performance optimization if needed
  - [ ] Cross-browser testing

- **Day 15**:
  - [ ] Create IMPLEMENTATION.md
  - [ ] Create TESTING.md
  - [ ] Create USAGE.md
  - [ ] Create COMPLETION.md (3 sign-offs)
  - [ ] Update README.md
  - [ ] Tag v0.1.0 and push
  - [ ] **Milestone: Phase complete & released ✅**

---

## Team & Resources

### Team
- **Frontend Lead**: 1 person (80 hours)
- **Backend Support**: 0.5 person (API endpoints)
- **QA**: Shared (testing & verification)

### Environment
- Node.js 18+
- npm or yarn
- CloudPlatform API running on localhost:8000
- Git repository: https://github.com/shreyashnadage/project-k-panel.git

### Tech Links
- Next.js: https://nextjs.org/docs
- React Query: https://tanstack.com/query/
- Tailwind CSS: https://tailwindcss.com/
- Recharts: https://recharts.org/

---

## Dependencies

### On Other Phases
- **Phase 0 (Backend)**: MUST be complete
  - CloudPlatform API endpoints functional
  - `/api/dashboard/*` endpoints returning data
  - CORS enabled for localhost:3000

### External Services
- **CloudPlatform API** (localhost:8000)
- **npm packages** (installed via package.json)

---

## Known Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Devanagari text rendering | Medium | High | Test with Hindi names early (Day 3) |
| API delays | Low | Medium | Cache with React Query, implement skeleton loaders |
| Performance with 100K records | Medium | High | Virtual scrolling, pagination, lazy loading (Day 10) |
| Browser compatibility | Low | Medium | Test on all 4 major browsers by Day 14 |
| Tailwind CSS issues | Low | Low | Use tested v4 setup, reference docs |

---

## Definition of Done

Phase 0-1 is DONE when:

✅ **Code**:
- All features implemented
- Code reviewed & approved
- ESLint: 0 errors, TypeScript: 0 errors
- Tests passing (80%+ coverage)

✅ **Quality**:
- Lighthouse 85+
- WCAG 2.1 AA compliant
- No console errors
- Cross-browser verified

✅ **Documentation**:
- PLAN.md ✅ (this file)
- IMPLEMENTATION.md created
- TESTING.md created
- USAGE.md created
- COMPLETION.md created (3 sign-offs)
- README.md updated

✅ **Release**:
- Tag v0.1.0 created
- Pushed to remote
- Ready for pilot deployment

---

## Next Phase

After Phase 0-1 completes:

**PHASE_2: Financial Visualization & Advanced Charting**
- 5+ financial widgets (waterfall, aging, heatmap)
- Apache Superset SQL dashboards
- Plotly.js for candlestick charts
- Real-time data sync

---

## Approval

**Status**: Ready for implementation  
**Approval**: Pending

- [ ] Product Manager: __________ (Date: __)
- [ ] Engineering Lead: __________ (Date: __)
- [ ] QA Lead: __________ (Date: __)

---

**Next**: Engineering team reads GOVERNANCE_LIGHTWEIGHT.md, then starts implementation following this plan.

Go build! 🚀
