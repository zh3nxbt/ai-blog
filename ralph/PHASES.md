# Ralph Wiggum Implementation Phases

## Phase 0: Vertical Spike ⏳ IN PROGRESS

**Goal:** Prove that Claude + Supabase + RSS integration works end-to-end

**Exit Criteria:**
- [x] Database schema complete (5 tables, indexes, seed data)
- [x] Migration tooling simplified and documented
- [ ] spike.py runs 3 times successfully
- [ ] 3 blog drafts created in Supabase
- [ ] RSS feeds return valid, parseable content
- [ ] Claude API generates readable blog posts
- [ ] Token costs measured and within budget (<$0.50/run)

**Deliverable:** Confidence that the system CAN work

**Duration:** Days 1-3 (estimated)

**Tasks:** spike-001 through spike-004 in PRD.json

---

## Phase 1: Core Ralph Loop (NEXT)

**Goal:** Build production worker with iterative content refinement

**Prerequisites:** Phase 0 complete

**Exit Criteria:**
- [ ] worker.py implements full generate-critique-refine loop
- [ ] Quality scoring system operational (0.0-1.0 scale)
- [ ] AI slop detection working (forbidden keywords)
- [ ] 5 published posts with quality >= 0.85
- [ ] Average 2-4 iterations per post
- [ ] Zero AI slop in published content
- [ ] Cost <= $0.25 per post
- [ ] Idempotent execution (safe to re-run)

**Deliverable:** Working production system (manual trigger)

**Duration:** Days 4-14 (estimated)

**Tasks:** Remaining tasks in PRD.json (services, ralph_core, functional, testing, documentation)

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

**Active Phase:** Phase 0 (Vertical Spike)

**Completed:**
- ✅ Database schema setup (db-001 through db-007)
- ✅ Migration tooling consolidation

**In Progress:**
- ⏳ Documentation updates (spike.py integrated into PRD)
- ⏳ spike.py implementation (pending)

**Next Up:**
- Build spike.py services (spike-001, spike-002)
- Create spike.py orchestrator (spike-003)
- Execute and verify (spike-004)
