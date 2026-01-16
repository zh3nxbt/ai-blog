# Ralph Wiggum Implementation Phases

## Phase 0: Vertical Spike ✅ COMPLETE

**Goal:** Prove that Claude + Supabase + RSS integration works end-to-end

**Exit Criteria:**
- [x] Database schema complete (5 tables, indexes, seed data)
- [x] Migration tooling simplified and documented
- [x] spike.py runs 3 times successfully
- [x] 3 blog drafts created in Supabase
- [x] RSS feeds return valid, parseable content
- [x] Claude API generates readable blog posts
- [x] Token costs measured and within budget (<$0.50/run)

**Deliverable:** Confidence that the system CAN work

**Duration:** Days 1-3 (estimated)

**Tasks:** spike-001 through spike-004 in PRD.json

**Completed:** 2026-01-13

**Results:**
- Average cost per post: $0.18 (well under $0.50 budget)
- Average duration: 57 seconds
- Average token usage: 1127 input + 2131 output = 3258 total
- 4 blog drafts created successfully
- RSS feeds demonstrated as reliable
- End-to-end integration validated

---

## Phase 1: Core Ralph Loop ⏳ IN PROGRESS

**Goal:** Build production worker with iterative content refinement

**Prerequisites:** Phase 0 complete ✅

**Exit Criteria:**
- [ ] `python -m ralph.ralph_loop` implements full generate-critique-refine loop
- [ ] Quality scoring system operational (0.0-1.0 scale)
- [ ] AI slop detection working (forbidden keywords)
- [ ] 5 published posts with quality >= 0.85
- [ ] Average 2-4 iterations per post
- [ ] Zero AI slop in published content
- [ ] Cost <= $0.50 per post
- [ ] Idempotent execution (safe to re-run, skips if post exists today)

**Deliverable:** Working production system (manual trigger)

**Duration:** Days 4-14 (estimated)

**Tasks:** Remaining tasks in PRD.json (services, ralph_core, functional, testing, documentation)

**Note:** The legacy `worker.py` stub has been removed. Use `python -m ralph.ralph_loop` which delegates to the full implementation in `ralph_content/ralph_loop.py`.

---

## Phase 2: Production Deployment (FUTURE)

**Goal:** Automate daily blog generation at 7 AM UTC

**Prerequisites:** Phase 1 complete

**Exit Criteria:**
- [ ] systemd timer configured for daily execution
- [ ] Email alerts on failures
- [ ] Monitoring dashboard operational
- [ ] 5 consecutive successful automated days
- [ ] No manual intervention required

**Deliverable:** Fully automated daily blog generation

**Duration:** Days 15-21 (estimated)

---

## Phase 3: Multi-Agent System (FUTURE)

**Goal:** Add TrendScout and Research agents for enhanced content

**Prerequisites:** Phase 2 complete

**Exit Criteria:**
- [ ] TrendScout agent identifies manufacturing trends
- [ ] Research agent gathers deeper context
- [ ] Multi-agent coordination working
- [ ] Quality improvement: +5-10% vs Phase 1
- [ ] Cost stays under $0.30/post

**Deliverable:** Enhanced content quality through multi-agent collaboration

**Duration:** Days 22-35 (estimated)

---

## Phase 4: Monitoring & Hardening (FUTURE)

**Goal:** Production-grade observability and reliability

**Prerequisites:** Phase 3 complete

**Exit Criteria:**
- [ ] Comprehensive test suite passing
- [ ] Documentation complete
- [ ] Monitoring operational
- [ ] Error recovery mechanisms tested
- [ ] Performance optimizations applied

**Deliverable:** Production-ready, battle-hardened system

**Duration:** Days 36-42 (estimated)

---

## Phase Progression Rules

1. **No phase skip:** Must complete all exit criteria before moving to next phase
2. **Document learnings:** Update progress.txt with insights from each phase
3. **Spike first:** Always build proof-of-concept before full implementation
4. **Fail fast:** If Phase 0 reveals fundamental issues, pivot early
5. **Quality gates:** Phase 1 quality thresholds must be met before automation (Phase 2)

---

## Current Status

**Active Phase:** Phase 1 (Core Ralph Loop)

**Completed:**
- ✅ Phase 0: Vertical Spike (2026-01-13)
  - Database schema setup (db-001 through db-007)
  - Migration tooling consolidation
  - spike.py implementation and validation (spike-001 through spike-004)

**In Progress:**
- ⏳ Phase 1: Core Ralph Loop implementation
  - ✅ Quality validation system (svc-008 through svc-012)
  - ✅ Agent framework (ralph-001 through ralph-011)
  - ✅ Iterative refinement loop (func-001 through func-007)
  - ✅ Mixed-source selection (mix-001 through mix-005)
  - ⏳ Validation with 5 published posts (test-001 through test-006)

**Remaining to complete Phase 1:**
- Generate 5th published post (currently have 4)
- Verify all test criteria pass
