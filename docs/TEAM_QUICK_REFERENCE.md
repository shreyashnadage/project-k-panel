# Team Quick Reference Card
## Documentation, Testing & Git Workflow Rules

**Print this. Tape it to your monitor. Follow it.** 📋

---

## 🏗️ DIRECTORY STRUCTURE

```
docs/
├── phases/PHASE_X/
│   ├── PHASE_X_PLAN.md              ← Start here (requirements)
│   ├── PHASE_X_IMPLEMENTATION.md     ← Daily progress log
│   ├── WEEKLY_PROGRESS_WEEK_N.md     ← Every Friday
│   ├── PHASE_X_TESTING.md            ← Test results
│   ├── PHASE_X_USAGE_GUIDE.md        ← How to use
│   ├── PHASE_X_COMPLETION.md         ← Sign-off (when done)
│   └── CHECKLIST.md                  ← Track progress
├── architecture/                      ← System design docs
├── testing/                           ← Test plans & benchmarks
├── guides/                            ← Developer guides
└── README.md                          ← Updated per phase
```

**RULE: ALL docs go in docs/ directory**

---

## 📝 DOCUMENT NAMING

| Document | Name Format | When |
|----------|-------------|------|
| Planning | `PHASE_X_PLAN.md` | Week 1 |
| Implementation | `PHASE_X_IMPLEMENTATION.md` | Week 2-3 |
| Weekly Progress | `WEEKLY_PROGRESS_WEEK_N.md` | Every Friday |
| Testing | `PHASE_X_TESTING.md` | Week 3 |
| Usage | `PHASE_X_USAGE_GUIDE.md` | Week 3 |
| Completion | `PHASE_X_COMPLETION.md` | End of phase |

**RULE: Use CAPS with underscores (not camelCase or spaces)**

---

## ✅ PHASE COMPLETION GATES

**Before marking phase COMPLETE, you need:**

### Gate 1: Code ✅
```
[ ] Features implemented
[ ] Code reviewed
[ ] ESLint: 0 errors
[ ] TypeScript: 0 errors
[ ] No console errors
```

### Gate 2: Testing ✅
```
[ ] Unit tests: 80%+ coverage
[ ] Integration tests: all pass
[ ] E2E tests: critical paths pass
[ ] Lighthouse: 85+
[ ] WCAG 2.1 AA: compliant
```

### Gate 3: Documentation ✅
```
[ ] PLAN.md complete
[ ] IMPLEMENTATION.md complete
[ ] TESTING.md complete
[ ] USAGE_GUIDE.md complete
[ ] COMPLETION.md complete
[ ] README.md updated
```

### Gate 4: Sign-Off ✅
```
[ ] Product Manager approval
[ ] Engineering Lead approval
[ ] QA Lead approval
[ ] All in COMPLETION.md with dates
```

**RULE: Missing even ONE checkbox = NOT COMPLETE**

---

## 🧪 TESTING CHECKLIST

**Before you consider work "done", you must pass:**

### Unit Tests
```bash
npm run test:unit
# Target: 80%+ coverage
# File: tests/unit/
```

### Integration Tests
```bash
npm run test:integration
# File: tests/integration/
```

### Manual Testing
```
Chrome   → [ ] Works
Firefox  → [ ] Works
Safari   → [ ] Works
Edge     → [ ] Works
Mobile   → [ ] Responsive
Dark     → [ ] Correct colors
```

### Performance
```
Lighthouse → [ ] 85+
Load Time  → [ ] < 2 seconds
Bundle     → [ ] < 150KB gzipped
```

**RULE: All tests must PASS before pushing**

---

## 🔄 GIT WORKFLOW

### Daily (End of Day)
```bash
# Commit with good message
git commit -m "[feat] widgets: Add KPI widget"

# Push to remote
git push origin phase/0-1
```

### After Phase Completes
```bash
# Update COMPLETION.md
git commit -m "[docs] phase-0-1: Add COMPLETION.md (signed off)"

# Update README
git commit -m "[docs] update README.md (Phase 0-1 complete)"

# Push everything
git push origin phase/0-1
git push origin staging
git push origin --tags

# Tag the release
git tag -a v0.1.0 -m "Phase 0-1 Complete"
```

**RULE: Push code EVERY DAY and at phase completion**

---

## 💬 COMMIT MESSAGE FORMAT

```
[TYPE] SCOPE: Description
```

**Types**:
- `[feat]` = New feature
- `[fix]` = Bug fix
- `[test]` = Test addition
- `[docs]` = Documentation
- `[refactor]` = Code refactoring
- `[perf]` = Performance improvement

**Examples**:
```
✅ [feat] widgets: Add KPI widget with real data
✅ [test] dashboard: Add 45 test cases
✅ [docs] phase-0-1: Update README with completion
❌ Bad: "Update stuff"
❌ Bad: "Fix bug"
```

**RULE: Commit messages must be descriptive**

---

## 📋 WEEKLY PROGRESS REPORT

**Every Friday EOD, create/update**: `WEEKLY_PROGRESS_WEEK_N.md`

```markdown
# Phase X — Week N Progress Report

**Week of**: [Date Range]  
**Status**: 🟢 On Track / 🟡 At Risk / 🔴 Blocked

## Completed This Week
- [x] Task 1
- [x] Task 2

## In Progress
- [ ] Task 3

## Blockers
- Blocker 1: Status

## Next Week
- Task 4
```

Then push:
```bash
git add WEEKLY_PROGRESS_WEEK_N.md
git commit -m "[docs] phase-x: Add weekly progress report"
git push origin phase/x
```

**RULE: Every Friday, push progress to remote**

---

## 📖 README UPDATE

**After EACH phase completion**, update `docs/README.md`:

```markdown
# Tally Sync Dashboard

**Last Updated**: 28 June 2026  
**Status**: Phase 0-1 ✅ | Phase 2 🚀

## Current Phase: Phase 0-1

| Phase | Status | Links |
|-------|--------|-------|
| **0-1** | ✅ COMPLETE | [Plan](phases/PHASE_0-1/PHASE_0-1_PLAN.md) |
| **2** | 🚀 READY | [Plan](phases/PHASE_2/PHASE_2_PLAN.md) |

### What Phase 0-1 Delivered
- ✅ Modular widgets
- ✅ 3 core widgets
- ✅ Dark theme
- ✅ Real API integration

### Phase 0-1 Results
- Bundle: 145KB
- Load Time: 1.8s
- Tests: 92% passing
- Lighthouse: 92/100

[Full Details](phases/PHASE_0-1/PHASE_0-1_COMPLETION.md)
```

**RULE: Update README after EVERY phase completion**

---

## 🎯 DEFINITION OF "DONE"

A phase is DONE when:

✅ All features built  
✅ All tests pass (80%+ coverage)  
✅ Lighthouse 85+  
✅ WCAG 2.1 AA  
✅ All 5 docs complete (PLAN, IMPLEMENTATION, TESTING, USAGE, COMPLETION)  
✅ README updated  
✅ PM, Eng Lead, QA signed off in COMPLETION.md  
✅ Code merged to staging  
✅ Version tag created (v0.1.0, v0.2.0, etc.)  
✅ Pushed to remote  

**If ANY item is missing: NOT DONE. Document blocker.**

---

## 🚫 COMMON MISTAKES (DON'T DO THIS)

| Mistake | Consequence | How to Fix |
|---------|-------------|-----------|
| Skip testing | Phase fails QA gate | Write tests first, then code |
| No daily commits | Hard to track progress | Commit daily, push to remote |
| Vague commit msgs | Blame history is useless | Use format: `[TYPE] SCOPE: Desc` |
| Docs outside docs/ | Can't find anything | Always use docs/ directory |
| Missing sign-offs | Can't release | Get all 3 approvals in COMPLETION.md |
| No weekly progress | PM loses trust | Every Friday, update WEEKLY_PROGRESS |
| Update README late | Users see old info | Update README immediately after phase |
| Push to main directly | Breaks production | Always merge via staging first |

---

## 📞 IF YOU GET STUCK

| Question | Answer |
|----------|--------|
| "Where do I save docs?" | `docs/phases/PHASE_X/` |
| "What tests do I write?" | See TEST_PLAN.md in docs/testing/ |
| "How do I commit?" | `[TYPE] SCOPE: Description` |
| "When do I push?" | Every day EOD + phase completion |
| "How do I know if I'm done?" | Check DEFINITION OF "DONE" above |
| "What's the README about?" | It's the first thing anyone reads |
| "Can I skip testing?" | NO. 80%+ coverage required |
| "Do I need sign-offs?" | YES. Three people must approve |

**Still stuck?** Check `docs/PROJECT_GOVERNANCE.md` (full rules)

---

## 🎬 QUICK START (First 5 Minutes)

```bash
# 1. Clone repo
git clone <repo>

# 2. Read this file
cat docs/TEAM_QUICK_REFERENCE.md

# 3. Read governance
cat docs/PROJECT_GOVERNANCE.md

# 4. For current phase, read PLAN
cat docs/phases/PHASE_X/PHASE_X_PLAN.md

# 5. Set up environment
npm install
npm run dev

# 6. Start coding!
# Remember: Commit daily, test often, document everything
```

---

## 📊 CHECKLIST: Before Saying "I'm Done"

```
Code
[ ] Features work
[ ] Reviewed by 1+ person
[ ] ESLint: 0 errors
[ ] TypeScript: 0 errors
[ ] No console errors

Testing  
[ ] Unit tests: 80%+ coverage
[ ] All tests passing
[ ] Lighthouse: 85+
[ ] Keyboard navigation works
[ ] Screen reader friendly

Docs
[ ] Commit daily (with good messages)
[ ] IMPLEMENTATION.md updated
[ ] USAGE_GUIDE.md updated
[ ] TESTING.md updated
[ ] Weekly progress report submitted

Git
[ ] Push to remote daily
[ ] No merge conflicts
[ ] Commit history is clean
[ ] Message format correct

Sign-Off (Only for phase completion)
[ ] PM approved
[ ] Eng Lead approved
[ ] QA approved
[ ] All signatures in COMPLETION.md
```

**If ANY box is unchecked: NOT DONE. Fix it first.**

---

## 🎓 TRAINING LINKS

- **Full Rules**: `docs/PROJECT_GOVERNANCE.md`
- **Phase Planning**: `docs/phases/PHASE_X/PHASE_X_PLAN.md`
- **Setup Help**: `docs/guides/DEVELOPER_SETUP.md`
- **Widget Dev**: `docs/guides/WIDGET_DEVELOPMENT_GUIDE.md`
- **Testing Guide**: `docs/testing/TEST_PLAN.md`
- **Architecture**: `docs/architecture/SYSTEM_ARCHITECTURE.md`

---

## ✍️ FINAL REMINDERS

1. **Docs are not optional** — They're how the team stays aligned
2. **Tests before code** — Write tests, THEN implement
3. **Commit daily** — So we can see progress
4. **Push to remote** — Daily + phase completion
5. **Update README** — First thing people read
6. **Get sign-offs** — Three people must approve
7. **Pass all gates** — Can't proceed without them
8. **Follow the structure** — Consistency saves time

---

**Last Updated**: 28 June 2026  
**Version**: 1.0  
**Status**: ACTIVE - All team members must follow

**Questions? See PROJECT_GOVERNANCE.md or create an issue.** 🚀
