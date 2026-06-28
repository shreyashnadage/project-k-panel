# Phase Template Pack
## Copy & Paste Templates for Every Phase

**Use these templates to start a new phase.** Just copy, rename, and fill in.

---

## 1. PHASE_X_PLAN.md Template

```markdown
# Phase X: [Feature Name]

**Document Type**: Plan  
**Phase**: X (Weeks N-M)  
**Owner**: [Your Name] ([Role])  
**Status**: In Progress  
**Last Updated**: YYYY-MM-DD  
**Git Commit**: [hash, add later]

---

## Executive Summary

[2-3 sentence overview of what this phase delivers]

Example:
"Phase 0-1 builds the foundation for a modular fintech dashboard. We'll create a widget registry system, implement 3 core financial widgets (KPI, Chart, Table), and integrate with the CloudPlatform API. By week 3, we'll have a pilot-ready dashboard ready for 5-10 MSME partners."

---

## Requirements & Specifications

### What Are We Building?
- Feature 1: [Description]
- Feature 2: [Description]
- Feature 3: [Description]

### Why Are We Building It?
[Business justification, customer need, etc.]

### Who Needs It?
[User personas: MSME accountants, finance managers, admins, etc.]

### Success Criteria
- [x] Criterion 1
- [x] Criterion 2
- [x] Criterion 3

---

## Technical Specifications

### Architecture Changes
[What's new in the architecture?]

### New Endpoints/Components
- Endpoint 1: `GET /api/dashboard/kpis`
- Component 1: `<KPIWidget />`
- Component 2: `<CashFlowChart />`

### Database Changes
- New table: `widget_config`
- New column in `tenants`: `default_layout`

### Breaking Changes
- [None expected] OR [List breaking changes]

---

## Dependencies

### External Services
- [Service 1]: [What we need from it]
- [Service 2]: [What we need from it]

### New Libraries to Install
```bash
npm install recharts @tanstack/react-query zustand
```

### Other Phases This Depends On
- Phase 0: Backend API setup (required)

### Phases That Depend On This
- Phase 2: Advanced charting (will depend on widget system)

---

## Timeline

### Week N (Planning & Setup)
- [ ] Day 1: Environment setup, repo initialization
- [ ] Day 2: Project structure, tooling
- [ ] Day 3: Team kickoff, architecture alignment
- [ ] Day 4: Dependency installation, basic setup
- [ ] Day 5: Buffer day, review progress

**Deliverable**: Development environment ready

### Week N+1 (Implementation)
- [ ] Day 6: Feature 1 implementation starts
- [ ] Day 7: Feature 1 continues
- [ ] Day 8: Feature 2 implementation starts
- [ ] Day 9: Feature 2 & 3 implementation
- [ ] Day 10: Integration, bug fixes

**Deliverable**: All features implemented

### Week N+2 (Testing & Documentation)
- [ ] Day 11: Testing setup, test cases
- [ ] Day 12: Unit tests, integration tests
- [ ] Day 13: Documentation, usage guide
- [ ] Day 14: Performance optimization, accessibility
- [ ] Day 15: Sign-off, completion report

**Deliverable**: Tested, documented, signed off

---

## Acceptance Criteria

### Feature 1: [Name]
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

### Feature 2: [Name]
- [ ] Requirement 1
- [ ] Requirement 2

### Testing
- [ ] 80%+ unit test coverage
- [ ] All integration tests pass
- [ ] Lighthouse score 85+
- [ ] WCAG 2.1 AA compliant

### Documentation
- [ ] IMPLEMENTATION.md complete
- [ ] TESTING.md complete
- [ ] USAGE_GUIDE.md complete
- [ ] README.md updated

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Devanagari text rendering issues | Medium | Medium | Early testing with Hindi names |
| API response delay | High | Low | Cache with React Query |
| Performance with 100K records | High | Medium | Virtual scrolling + pagination |

---

## Resources & Team

**Team Members**:
- [Name] - Frontend Lead
- [Name] - Backend Support
- [Name] - QA

**Tools**:
- Repository: [GitHub link]
- Project Board: [Linear/Jira link]
- Slack Channel: [#channel-name]

---

## Next Steps (After Approval)

1. [ ] Get PM approval
2. [ ] Get Engineering Lead approval
3. [ ] Create feature branches
4. [ ] Begin implementation (Week 1)
5. [ ] Daily commits & pushes
6. [ ] Weekly progress reports

---

**Status**: Pending Approval  
**Approval Gates**: PM ⬜ | Eng Lead ⬜ | QA ⬜

---

## Sign-Off (After Review)

- [ ] Product Manager Approval: __________ (Date: __)
- [ ] Engineering Lead Approval: __________ (Date: __)
- [ ] QA Lead Approval: __________ (Date: __)
```

---

## 2. PHASE_X_IMPLEMENTATION.md Template

```markdown
# Phase X: Implementation Progress

**Document Type**: Implementation  
**Phase**: X  
**Owner**: [Your Name]  
**Status**: In Progress  
**Last Updated**: YYYY-MM-DD

---

## Daily Progress Log

### 📅 Day 1 (Date: YYYY-MM-DD)

**Tasks Completed**:
- ✅ Task 1: [Description] → [Commit: abc1234]
- ✅ Task 2: [Description] → [Commit: abc1235]

**In Progress**:
- 🔄 Task 3: [Description] (Est. completion: tomorrow)

**Blockers**: None

**Notes**: Setup complete, team aligned on architecture

---

### 📅 Day 2 (Date: YYYY-MM-DD)

**Tasks Completed**:
- ✅ Task 3: [Description] → [Commit: abc1236]

**In Progress**:
- 🔄 Task 4: [Description]

**Blockers**: 
- 🚫 API endpoint not returning expected data format
- Mitigation: Contact backend team, created workaround

**Notes**: Good progress, one blocker resolved

---

## Code Changes Summary

### Files Created
- `src/lib/widgetRegistry.ts` - Widget registry system
- `src/components/widgets/KPIWidget.tsx` - KPI component
- `src/components/widgets/ChartWidget.tsx` - Chart component
- `tests/unit/widgets/*.test.tsx` - Unit tests

### Files Modified
- `src/pages/dashboard.tsx` - Added widget container
- `.env.example` - Added API URLs

### Database Migrations
```sql
-- Added widget_config table
CREATE TABLE widget_config (...)
```

### Configuration Changes
```bash
# Environment variables
NEXT_PUBLIC_API_URL=http://localhost:8000
REACT_QUERY_CACHE_TIME=300000
```

---

## Issues Encountered & Resolution

### Issue 1: Devanagari Text Rendering
**Problem**: Hindi company names breaking layout  
**Root Cause**: Missing font stack  
**Solution**: Added `Noto Sans Devanagari` to Tailwind config  
**Commit**: abc1237  
**Status**: ✅ Resolved

### Issue 2: React Query Cache Performance
**Problem**: Stale data in dashboard  
**Root Cause**: Cache time too long (5 min)  
**Solution**: Reduced to 30 seconds, added manual invalidation  
**Commit**: abc1238  
**Status**: ✅ Resolved

---

## Screenshots & Demo

### Widget Registry System
[Add screenshot]

### Dashboard with Widgets
[Add screenshot]

### Dark Mode Rendering
[Add screenshot]

---

## Code Review Status

- [x] PR Created: [Link to PR]
- [x] Reviewer 1 Approved: [Name]
- [x] Reviewer 2 Approved: [Name]
- [x] Ready to Merge: [Yes/No]

**Review Comments**:
- Feedback 1: [How addressed]
- Feedback 2: [How addressed]

---

## Performance Metrics (Before/After Implementation)

| Metric | Before | After | Change | Status |
|--------|--------|-------|--------|--------|
| Bundle Size | - | 145KB | - | ✅ |
| Load Time | - | 1.8s | - | ✅ |
| Paint Time | - | 1.2s | - | ✅ |
| First Input Delay | - | 80ms | - | ✅ |

---

## Next Steps

- [ ] Complete remaining features (Day X)
- [ ] Start testing phase (Week Y)
- [ ] Get code review approvals
- [ ] Update USAGE_GUIDE.md

---

**Last Updated**: YYYY-MM-DD  
**Next Update**: Tomorrow EOD
```

---

## 3. PHASE_X_TESTING.md Template

```markdown
# Phase X: Testing Results

**Document Type**: Testing  
**Phase**: X  
**Owner**: [QA Lead Name]  
**Status**: In Progress  
**Last Updated**: YYYY-MM-DD

---

## Test Scope

**What We're Testing**:
- Feature 1: [Description]
- Feature 2: [Description]
- Feature 3: [Description]

**What We're NOT Testing**:
- Backend API (assumed working)
- Browser extensions
- Extremely slow networks

**Test Environment**:
- OS: Windows 11 / macOS 14 / Ubuntu 22.04
- Browser: Chrome 120+, Firefox 121+, Safari 17+, Edge 120+
- Network: Modern broadband (50+ Mbps)
- Devices: Desktop, Laptop, Tablet, Phone

---

## Test Cases

### Feature 1: KPI Widget

#### TC-1: Widget Renders with Data
```
Test Case ID: TC-1
Title: KPI Widget displays correct data
Preconditions:
  - Dashboard open
  - API returning mock KPI data
  
Steps:
  1. Navigate to Dashboard page
  2. Wait for KPI Widget to load
  3. Verify numbers display correctly
  
Expected Result:
  - Widget renders in < 1 second
  - Numbers formatted with commas (₹23,45,000)
  - No console errors
  
Actual Result:
  ✅ PASS - All assertions met
  
Duration: 12 seconds
```

#### TC-2: Widget Error State
```
Test Case ID: TC-2
Title: KPI Widget handles API errors gracefully
Preconditions:
  - API endpoint returning 500 error
  
Steps:
  1. Navigate to Dashboard
  2. Observe KPI Widget loading
  
Expected Result:
  - Error message displays
  - Retry button visible
  - No crash
  
Actual Result:
  ✅ PASS - Error handled cleanly
```

### Feature 2: Chart Widget

#### TC-3: Chart Renders
```
Test Case ID: TC-3
Title: Cash Flow chart renders without errors
Expected Result: ✅ PASS
```

---

## Unit Test Results

```bash
npm run test:unit

Test Files: 45 passed
✅ components/widgets/KPIWidget.test.tsx: 5 tests passed
✅ components/widgets/ChartWidget.test.tsx: 8 tests passed
✅ components/Dashboard.test.tsx: 12 tests passed
✅ lib/widgetRegistry.test.ts: 20 tests passed

Coverage:
  Statements: 92% ✅
  Branches: 88% ✅
  Functions: 94% ✅
  Lines: 91% ✅
```

---

## Integration Test Results

```bash
npm run test:integration

✅ Dashboard loads widget data
✅ API integration working
✅ Error handling functional
✅ Pagination working

Total: 12 tests, 12 passed, 0 failed
```

---

## Performance Testing Results

### Lighthouse Audit
```
Performance: 92 ✅ (target: 85+)
Accessibility: 96 ✅ (target: 90+)
Best Practices: 95 ✅ (target: 90+)
SEO: 100 ✅ (target: 90+)
```

### Load Time
```
First Contentful Paint: 1.2s ✅ (target: < 2s)
Largest Contentful Paint: 1.8s ✅ (target: < 2.5s)
Cumulative Layout Shift: 0.05 ✅ (target: < 0.1)
```

### Bundle Size
```
Gzipped: 145KB ✅ (target: < 150KB)
Uncompressed: 450KB
Largest chunks: Recharts (60KB)
```

---

## Accessibility Testing (WCAG 2.1 AA)

- [x] Keyboard navigation works (Tab, Shift+Tab, Enter)
- [x] Screen reader compatible (tested with NVDA)
- [x] Color contrast 4.5:1+ (all text)
- [x] Form labels present
- [x] Focus indicators visible
- [x] No color-only information

**Status**: ✅ WCAG 2.1 AA Compliant

---

## Browser Compatibility

| Browser | Version | Dashboard | Widget 1 | Widget 2 | Status |
|---------|---------|-----------|----------|----------|--------|
| Chrome | 120 | ✅ | ✅ | ✅ | PASS |
| Firefox | 121 | ✅ | ✅ | ✅ | PASS |
| Safari | 17 | ✅ | ✅ | ✅ | PASS |
| Edge | 120 | ✅ | ✅ | ✅ | PASS |

**Mobile**:
| Browser | Device | Status |
|---------|--------|--------|
| Chrome | iPhone 15 | ✅ PASS |
| Chrome | Android 14 | ✅ PASS |
| Safari | iPad Air | ✅ PASS |

---

## Test Summary

### Metrics
- **Total Test Cases**: 45
- **Passed**: 45 ✅
- **Failed**: 0 ❌
- **Blocked**: 0 ⚠️
- **Pass Rate**: 100% ✅

### Coverage
- **Code Coverage**: 92% ✅ (target: 80%+)
- **Feature Coverage**: 100% ✅
- **Edge Cases**: Covered ✅

### Overall Status: ✅ ALL TESTS PASS

---

## Known Issues & Workarounds

### Issue 1: Hindi Text in Small Containers
**Severity**: Low  
**Workaround**: Use min-width container  
**Fix Timeline**: Phase 2  

### Issue 2: Slow Network Performance
**Severity**: Low  
**Workaround**: Implement skeleton loaders  
**Fix Timeline**: Phase 2  

**Critical Issues**: None ✅

---

## Recommendations

1. ✅ **Ready for Production**: All tests pass, no blockers
2. ⚠️ Monitor Hindi text rendering in edge cases
3. ✅ Performance is excellent, no optimization needed

---

## Sign-Off

- [x] QA Lead Approval: [Name] (Date: __)
- [x] Engineering Lead Review: [Name] (Date: __)

**Final Status**: ✅ APPROVED FOR RELEASE

---

**Last Updated**: YYYY-MM-DD  
**Next Phase**: Deployment
```

---

## 4. PHASE_X_USAGE_GUIDE.md Template

```markdown
# Phase X: User & Developer Guide

**Document Type**: Usage Guide  
**Phase**: X  
**Status**: Complete

---

## For End Users (MSME Accountants)

### Feature 1: Dashboard Overview

#### How to Access
1. Open http://localhost:3000 (or your domain)
2. Log in with your MSME credentials
3. Click "Dashboard" in sidebar

#### What You See
- KPI cards showing total records
- Cash flow chart
- Recent vouchers table

#### How to Use It
**View Your KPIs**:
- Look at top cards for summary
- Numbers update every 30 seconds

**Check Cash Flow**:
- Chart shows last 6 months
- Hover over bars for details
- Click to zoom

**Browse Vouchers**:
- Table shows recent transactions
- Sort by date, party, amount
- Export to CSV

**Screenshots**:
[Add annotated screenshots]

### Feature 2: [Name]

[Repeat above format]

---

## For Developers

### Setup

#### Prerequisites
```bash
Node.js 18+
npm or yarn
git
```

#### Installation
```bash
# Clone repo
git clone <repo>
cd tally-sync-dashboard

# Install dependencies
npm install

# Start dev server
npm run dev

# Open http://localhost:3000
```

#### Environment Configuration
```bash
# Copy .env.example
cp .env.example .env.local

# Edit .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_TENANT_ID=default-tenant
```

---

### API Endpoints

#### GET /api/dashboard/kpis
```bash
curl http://localhost:8000/api/dashboard/kpis?tenant_id=default

Response:
{
  "total_ledgers": 234,
  "total_vouchers": 12450,
  "last_sync": "2026-06-28T10:30:00Z",
  "sync_health": "healthy"
}
```

#### GET /api/dashboard/vouchers
```bash
curl "http://localhost:8000/api/dashboard/vouchers?tenant_id=default&skip=0&limit=50"

Response:
{
  "data": [
    {
      "id": 1,
      "voucher_number": "MRN-001",
      "date": "2026-06-28",
      "party": "Company Name",
      "amount": "23450.50",
      "type": "Sales"
    }
  ],
  "total": 12450,
  "skip": 0,
  "limit": 50
}
```

---

### Widget Development

#### Create New Widget

**Step 1**: Create component file
```typescript
// src/components/widgets/MyWidget.tsx
export default function MyWidget({ data }) {
  return <div>{/* your widget */}</div>
}
```

**Step 2**: Register in widget registry
```typescript
// src/lib/widgetRegistry.ts
export const WIDGET_DEFINITIONS = {
  my_widget: {
    id: 'my_widget',
    component: MyWidget,
    title: 'My Widget',
    // ... other config
  }
}
```

**Step 3**: Add to layout
```typescript
DEFAULT_LAYOUTS.admin.push({
  id: 'my_widget',
  order: 99,
  visible: true
})
```

#### Full Example
[Code example here]

---

### Troubleshooting

**Dashboard won't load**:
```
Check:
1. Is dev server running? (npm run dev)
2. Is port 3000 available?
3. Is API responding? (curl http://localhost:8000/health)
4. Are dependencies installed? (npm install)
```

**API connection error**:
```
Check:
1. Is .env.local configured?
2. Is API server running?
3. Is CORS enabled on backend?
```

**Chart not rendering**:
```
Check:
1. Is data loading? (open DevTools Network tab)
2. Are you using dynamic import?
3. Check browser console for errors
```

---

**For more help**: Check docs/guides/TROUBLESHOOTING.md

---

**Last Updated**: YYYY-MM-DD
```

---

## 5. PHASE_X_COMPLETION.md Template

```markdown
# Phase X: Completion Report

**Document Type**: Completion Report  
**Phase**: X (Weeks N-M)  
**Date Completed**: YYYY-MM-DD

---

## Executive Summary

**Phase X delivered [X features] on time and under budget.** All acceptance criteria met, all tests passing, all stakeholders signed off.

---

## Scope: What We Delivered

### ✅ Completed Features
- [x] Feature 1 - [Description]
- [x] Feature 2 - [Description]
- [x] Feature 3 - [Description]

### ⚠️ Partial/Deferred
- ⚠️ Feature 4 - Deferred to Phase X+1 (reason)

### ❌ Not Completed
- ❌ Feature 5 - Deprioritized (reason)

---

## Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Timeline** | 3 weeks | 3 weeks | ✅ |
| **Budget** | 80 hours | 78 hours | ✅ |
| **Quality** | 80% tests | 92% tests | ✅ |
| **Performance** | 85+ | 92 | ✅ |
| **Accessibility** | WCAG 2.1 AA | WCAG 2.1 AA | ✅ |

---

## Gate Criteria (All ✅)

### Code Quality
- [x] All features implemented
- [x] Code reviewed & approved
- [x] ESLint: 0 errors
- [x] TypeScript: 0 errors
- [x] No console errors

### Testing
- [x] 92% test coverage (target: 80%+)
- [x] 100% tests passing
- [x] Lighthouse: 92 (target: 85+)
- [x] WCAG 2.1 AA compliant
- [x] Cross-browser tested

### Documentation
- [x] PLAN.md complete
- [x] IMPLEMENTATION.md complete
- [x] TESTING.md complete
- [x] USAGE_GUIDE.md complete
- [x] README.md updated
- [x] API docs updated

### Version Control
- [x] All commits follow format
- [x] Feature branch merged
- [x] Staging branch updated
- [x] Main branch updated
- [x] Version tag created (v0.1.0)

---

## Lessons Learned

### What Went Well ✅
- Team collaboration was excellent
- Architecture decisions held up well
- Testing caught edge cases early
- Customer feedback was positive

### What We'd Do Differently ⚠️
- Could have started testing earlier
- Devanagari testing should happen in Week 1, not Week 3
- More frequent stakeholder syncs would help

### Technical Debt
- None accrued ✅

---

## Recommendations for Next Phase

1. Implement Apache Superset (dashboarding)
2. Add Plotly.js for financial charts
3. Expand widget library (5+ new widgets)

---

## Sign-Off

### Approvals Required (All ✅)

- [x] **Product Manager**
  - Name: [Name]
  - Signature: _____________
  - Date: YYYY-MM-DD
  - Comments: "Exceeds expectations"

- [x] **Engineering Lead**
  - Name: [Name]
  - Signature: _____________
  - Date: YYYY-MM-DD
  - Comments: "Code quality excellent"

- [x] **QA Lead**
  - Name: [Name]
  - Signature: _____________
  - Date: YYYY-MM-DD
  - Comments: "All tests pass, ready for production"

---

## Release Information

**Version**: v0.1.0  
**Git Tag**: v0.1.0  
**Release Date**: YYYY-MM-DD  
**Release Notes**: [Link to release notes]

**Deployment**:
- [ ] Staging deployment successful
- [ ] Production deployment scheduled
- [ ] Customer communication sent

---

## Next Phase Kickoff

**Phase 2 Starts**: YYYY-MM-DD  
**Phase 2 Owner**: [Name]  
**Phase 2 Details**: [Link to Phase 2 PLAN.md]

---

**STATUS**: ✅ PHASE X COMPLETE & RELEASED

---

**Last Updated**: YYYY-MM-DD  
**Prepared By**: [Name] ([Role])
```

---

## How to Use These Templates

1. **Create new phase directory**:
   ```bash
   mkdir -p docs/phases/PHASE_X
   ```

2. **Copy templates into directory**:
   ```bash
   # Copy this file and rename
   cp PHASE_TEMPLATE_PACK.md PHASE_X_PLAN.md
   # Edit and fill in bracketed sections
   ```

3. **Fill in brackets** `[like this]` with actual information

4. **Add to git** and push:
   ```bash
   git add docs/phases/PHASE_X/
   git commit -m "[docs] phase-x: Initialize phase documentation"
   git push origin phase/x
   ```

5. **Update as you work** (IMPLEMENTATION.md especially)

6. **Sign off** when phase complete (COMPLETION.md)

---

**Ready to go? Copy, fill in, and start documenting!** 📝
