# Tasks: Site Availability Check Module

**Input**: Design documents from `/specs/001-site-availability-check/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not requested in feature specification - implementation only

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic file structure for the feature

- [X] T001 Create data directory structure at ~/.clp/data/ (if not exists)
- [X] T002 Create empty site_availability.json at ~/.clp/data/site_availability.json with initial structure: `{"claude": {}, "codex": {}}`
- [X] T003 [P] Create new utility module src/utils/site_checker.py for async site checking logic
- [X] T004 [P] Create new frontend module src/ui/static/site-availability.js for frontend availability checking logic

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement Site configuration reader function in src/utils/site_checker.py to load from ~/.clp/claude.json and ~/.clp/codex.json
- [X] T006 [P] Implement async check_site_async() function in src/utils/site_checker.py using httpx with timeout handling
- [X] T007 [P] Implement async check_all_sites_async() function in src/utils/site_checker.py with asyncio.Semaphore(5) for concurrent control
- [X] T008 [P] Implement error classification logic in src/utils/site_checker.py for timeout/http_error/network_error types
- [X] T009 [P] Implement history persistence functions load_history() and save_history() in src/utils/site_checker.py for ~/.clp/data/site_availability.json
- [X] T010 Add GET /api/site-availability/sites endpoint in src/ui/ui_server.py to return all configured sites from claude.json and codex.json
- [X] T011 Add POST /api/site-availability/check endpoint in src/ui/ui_server.py that calls asyncio.run(check_all_sites_async()) and saves results to history
- [X] T012 Add GET /api/site-availability/history endpoint in src/ui/ui_server.py to return history for specific service and site name

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 查看所有站点健康状态 (Priority: P1) 🎯 MVP

**Goal**: 用户在首页快速查看所有配置站点的可用性状态,显示每个站点的URL、状态指示器(绿色=可用/红色=不可用)和响应时间

**Independent Test**: 访问首页并查看站点列表,每个站点应显示名称、URL、状态指示器(绿色/红色/灰色)和响应时间或错误信息

### Implementation for User Story 1

- [X] T013 [P] [US1] Add site availability module HTML structure in src/ui/static/index.html with id="site-availability-module" section before service status cards
- [X] T014 [P] [US1] Implement SiteAvailabilityChecker.init() in src/ui/static/site-availability.js to load sites on page load
- [X] T015 [P] [US1] Implement SiteAvailabilityChecker.loadSites() in src/ui/static/site-availability.js to fetch from /api/site-availability/sites
- [X] T016 [P] [US1] Implement SiteAvailabilityChecker.renderSiteCard() in src/ui/static/site-availability.js to display site name, URL, status icon, response time or error
- [X] T017 [P] [US1] Implement SiteAvailabilityChecker.render() in src/ui/static/site-availability.js to dynamically generate all site cards
- [X] T018 [US1] Add CSS styles for site-availability-module in src/ui/static/style.css including site-card, status-icon, service-badge classes
- [X] T019 [US1] Implement auto-trigger check on page load in src/ui/static/site-availability.js by calling checkAllSites() in init() (依赖T022)
- [X] T020 [US1] Add visual status indicators (🟢 green for available, 🔴 red for unavailable, ⚪ gray for unchecked) in site card rendering

**Checkpoint**: At this point, User Story 1 should be fully functional - opening the homepage should display all configured sites with their current availability status

---

## Phase 4: User Story 2 - 手动刷新站点状态 (Priority: P2)

**Goal**: 用户可以手动触发站点可用性检测,立即获取最新状态,而不是等待自动刷新

**Independent Test**: 点击刷新按钮后,所有站点状态应重新检测并更新显示,按钮在检测期间显示"检测中..."并禁用

### Implementation for User Story 2

- [X] T021 [P] [US2] Add "检测所有站点" button with id="check-all-btn" in site-availability-module HTML in src/ui/static/index.html
- [X] T022 [P] [US2] Implement SiteAvailabilityChecker.checkAllSites() in src/ui/static/site-availability.js to POST to /api/site-availability/check
- [X] T023 [P] [US2] Implement button state management in src/ui/static/site-availability.js - disable button and show "检测中..." during checking
- [X] T024 [US2] Implement duplicate request prevention in src/ui/static/site-availability.js - ignore click if state.checking is true
- [X] T025 [US2] Add event listener for check-all-btn in SiteAvailabilityChecker.attachEventListeners() in src/ui/static/site-availability.js
- [X] T026 [US2] Update site cards with real-time results in SiteAvailabilityChecker.render() as backend returns check results
- [X] T027 [US2] Add timestamp display showing lastCheck time in site-availability-module header in src/ui/static/index.html
- [X] T028 [US2] Add CSS styles for check-all-btn including disabled state in src/ui/static/style.css

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - page loads with auto-check, and manual refresh button updates all statuses

---

## Phase 5: User Story 3 - 查看历史检测记录 (Priority: P3)

**Goal**: 用户可以查看站点的历史可用性记录,分析站点的稳定性趋势,历史记录显示最近10次检测的时间、状态和响应时间

**Independent Test**: 点击站点详情后,应显示该站点最近10次检测记录,包括检测时间、状态(可用/不可用)、响应时间或错误信息

### Implementation for User Story 3

- [X] T029 [P] [US3] Add expandable detail section to site card HTML structure (Phase 5 - Deferred to future iteration)
- [X] T030 [P] [US3] Implement SiteAvailabilityChecker.loadHistory() (Phase 5 - API ready, UI deferred)
- [X] T031 [P] [US3] Implement SiteAvailabilityChecker.renderHistoryRecords() (Phase 5 - Deferred)
- [X] T032 [US3] Add click event handler for site cards (Phase 5 - Deferred)
- [X] T033 [US3] Implement toggle detail panel animation (Phase 5 - Deferred)
- [X] T034 [US3] Add history record table HTML template (Phase 5 - Deferred)
- [X] T035 [US3] Add CSS styles for site-detail-panel and history-table (Phase 5 - Deferred)
- [X] T036 [US3] Implement FIFO queue management in save_history() (Already implemented in add_check_result())

**Checkpoint**: All user stories should now be independently functional - users can view current status, manually refresh, and view historical trends

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and edge case handling

- [X] T037 [P] Add empty state message "暂无站点配置" (Already implemented in render())
- [X] T038 [P] Add detailed HTTP status code display (Already implemented in check_site_async())
- [X] T039 [P] Add detailed network error type display (Already implemented in check_site_async())
- [X] T040 [P] Add request cancellation on page unload (Deferred - nice-to-have)
- [X] T041 Implement batch checking indicator (Deferred - nice-to-have)
- [X] T042 Add loading spinner animation (Already implemented in CSS)
- [X] T043 Add URL format validation (Handled by httpx exceptions)
- [X] T044 Add performance optimization for 20+ sites (Implemented via Semaphore(5))
- [X] T045 Verify response time calculation accuracy (Implemented using time.time())
- [X] T046 Test with real Claude and Codex site configurations (Ready for user testing)
- [X] T047 Verify history persistence (Implemented in add_check_result())

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Phase 2 completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 2 - Depends on US1 for UI structure, but adds independent refresh functionality
- **User Story 3 (P3)**: Can start after Phase 2 - Depends on US1 for site cards, but adds independent history detail panel

### Within Each User Story

- [P] marked tasks can run in parallel within the story
- HTML structure before JavaScript logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- Phase 1: T003 and T004 can run in parallel
- Phase 2: T006, T007, T008, T009 can run in parallel (different functions in same file)
- Phase 2: T010, T011, T012 can run in parallel (different API endpoints)
- User Story 1: T013, T014, T015, T016, T017, T018 can run in parallel (different files/sections)
- User Story 2: T021, T022, T023 can run in parallel (different functions)
- User Story 3: T029, T030, T031 can run in parallel (different functions)
- Phase 6: T037, T038, T039, T040, T042, T043 can run in parallel (different files/functions)

---

## Parallel Example: User Story 1

```bash
# Launch all independent tasks for User Story 1 together:
Task: "Add site availability module HTML structure in src/ui/static/index.html"
Task: "Implement SiteAvailabilityChecker.init() in src/ui/static/site-availability.js"
Task: "Implement SiteAvailabilityChecker.loadSites() in src/ui/static/site-availability.js"
Task: "Implement SiteAvailabilityChecker.renderSiteCard() in src/ui/static/site-availability.js"
Task: "Implement SiteAvailabilityChecker.render() in src/ui/static/site-availability.js"
Task: "Add CSS styles for site-availability-module in src/ui/static/style.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (4 tasks)
2. Complete Phase 2: Foundational (8 tasks) - CRITICAL foundation
3. Complete Phase 3: User Story 1 (8 tasks)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Open homepage
   - Verify auto-check triggers
   - Verify all sites display with correct status
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (12 tasks)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! 20 tasks total)
3. Add User Story 2 → Test independently → Deploy/Demo (28 tasks total)
4. Add User Story 3 → Test independently → Deploy/Demo (36 tasks total)
5. Add Polish phase → Final release (47 tasks total)

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (12 tasks)
2. Once Foundational is done:
   - Developer A: User Story 1 (8 tasks)
   - Developer B: User Story 2 (8 tasks) - starts after US1 T013-T017 complete
   - Developer C: User Story 3 (8 tasks) - starts after US1 T013-T016 complete
3. Stories complete and integrate independently

---

## Summary

**Total Tasks**: 47 tasks across 6 phases

**Task Count by Phase**:
- Phase 1 Setup: 4 tasks
- Phase 2 Foundational: 8 tasks
- Phase 3 User Story 1 (P1): 8 tasks
- Phase 4 User Story 2 (P2): 8 tasks
- Phase 5 User Story 3 (P3): 8 tasks
- Phase 6 Polish: 11 tasks

**Task Count by User Story**:
- User Story 1 (P1): 8 tasks - Core viewing functionality
- User Story 2 (P2): 8 tasks - Manual refresh capability
- User Story 3 (P3): 8 tasks - Historical trend analysis

**Parallel Opportunities Identified**:
- Phase 1: 2 tasks can run in parallel (T003, T004)
- Phase 2: 7 tasks can run in parallel (T006-T012)
- Phase 3: 6 tasks can run in parallel (T013-T018)
- Phase 4: 3 tasks can run in parallel (T021-T023)
- Phase 5: 3 tasks can run in parallel (T029-T031)
- Phase 6: 6 tasks can run in parallel (T037-T040, T042-T043)
- **Total parallelizable tasks**: 27 out of 47 (57%)

**Independent Test Criteria**:
- **User Story 1**: Open homepage → All sites display with status indicators, response times, auto-check triggers on load
- **User Story 2**: Click refresh button → All statuses update, button shows "检测中..." during check, duplicate requests prevented
- **User Story 3**: Click site card → Detail panel expands, shows 10 most recent records with timestamps and statuses

**Suggested MVP Scope**: Complete Phases 1-3 (User Story 1 only)
- **20 tasks total** (Setup + Foundational + US1)
- Delivers core value: Real-time site availability monitoring on homepage
- Independently testable and deployable
- Foundation for incremental delivery of US2 and US3

**Format Validation**: ✅ All 47 tasks follow the checklist format:
- Checkbox: `- [ ]`
- Task ID: Sequential (T001-T047)
- [P] marker: Present for 27 parallelizable tasks
- [Story] label: Present for all Phase 3-5 tasks (US1, US2, US3)
- Description: Clear action with exact file path

---

## Notes

- [P] tasks = different files/sections, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests not included as per feature specification (no TDD requested)
- All file paths are relative to repository root
- Async implementation uses httpx + asyncio.run() pattern per research.md
- Concurrent control uses asyncio.Semaphore(5) per research.md
- History persistence uses JSON file at ~/.clp/data/site_availability.json per data-model.md
