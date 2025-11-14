# Production Readiness Fixes

**Created**: November 14, 2025  
**Status**: Planned  
**Priority**: High

## Overview

Address critical production readiness and code quality issues identified in the codebase diagnostic.

---

## Issues to Fix

### 1. Timezone-Naive Datetime Usage

**Priority:** CRITICAL  
**Effort:** 30 minutes  
**Impact:** Security, Data Integrity

**Problem:**
Using `datetime.utcnow()` (17 occurrences) creates naive datetime objects without timezone info, causing:
- Incorrect session expiry validation
- Ambiguous timestamps in database
- DST and timezone bugs

**Files Affected:**
- `backend/src/backend/db/models.py` (11 occurrences)
- `backend/src/backend/api/websocket.py` (3 occurrences)
- `backend/src/backend/auth/session.py` (1 occurrence)
- `backend/src/backend/api/settings.py` (1 occurrence)
- `backend/src/backend/api/conversations.py` (1 occurrence)

**Solution:**
Replace all `datetime.utcnow()` with `datetime.now(timezone.utc)`

---

### 2. Database Session Cleanup

**Priority:** CRITICAL  
**Effort:** 1 hour  
**Impact:** Stability, Memory Leaks

**Problem:**
20 calls to `get_db()` without explicit cleanup. WebSocket handlers are long-lived and may not trigger Flask's teardown context, leading to:
- Connection pool exhaustion
- Memory leaks
- Database locks

**Critical Location:**
- `backend/src/backend/api/websocket.py` (holds session for entire message processing)

**Solution:**
- Create `db_session()` and `db_transaction()` context managers
- Update WebSocket handler to use context managers (critical)
- Optionally update REST endpoints for consistency

---

### 3. Logging Infrastructure

**Priority:** HIGH  
**Effort:** 2-3 hours  
**Impact:** Observability, Operations

**Problem:**
Using `print()` statements (52 occurrences) instead of proper logging:
- Can't control log levels (DEBUG/INFO/ERROR)
- No log rotation or file management
- Can't integrate with monitoring tools
- Can't disable debug output in production

**Files Affected:**
All API and store modules (13 files total)

**Solution:**
- Create `logging_config.py` with rotating file handlers
- Initialize logging in `app.py`
- Replace all `print()` with `logger.info()`, `logger.error()`, etc.
- Use `exc_info=True` for exceptions

---

### 4. Centralized Configuration

**Priority:** MEDIUM  
**Effort:** 1-2 hours  
**Impact:** Maintainability, Tuning

**Problem:**
Magic numbers scattered in code:
- `n_results=10` (document search)
- `limit(10)` (message history)
- `timeout: 30000` (API timeout)
- `hours=24` (session expiry)

Hard to tune performance without editing code.

**Solution:**
- Create `config.sh` as single source of truth
- Add config values to `Config` class
- Update code to use `Config.RAG_MAX_DOCUMENT_RESULTS`, etc.
- Update setup/start scripts to source config.sh

---

### 5. Incomplete Feature Documentation

**Priority:** LOW  
**Effort:** 5 minutes  
**Impact:** Code Clarity

**Problem:**
Empty `@socketio.on('typing')` handler with no explanation of why it's incomplete.

**Solution:**
Add detailed docstring explaining:
- This is a placeholder for future multi-user support
- Not needed for single-user local deployment
- What it would do if implemented

---

### 6. Missing Test Suite

**Priority:** HIGH  
**Effort:** 4-6 hours  
**Impact:** Reliability, Regression Prevention

**Problem:**
No tests in the repository. No way to:
- Verify changes don't break functionality
- Catch regressions
- Document expected behavior
- Enable confident refactoring

**Areas Needing Tests:**
- Authentication (password hashing, session management)
- Document upload and processing
- RAG search functionality
- WebSocket message handling
- API endpoints (REST)
- Database models and relationships
- Memory/conversation search

**Solution:**
- Create `backend/tests/` structure with pytest
- Add unit tests for core functions
- Add integration tests for API endpoints
- Add fixtures for test data
- Configure pytest in `pyproject.toml`
- Add test command to documentation

**Test Priority:**
1. Authentication & sessions (security critical)
2. Document upload & embeddings (core feature)
3. WebSocket chat flow (core feature)
4. RAG search (core feature)
5. API endpoints (completeness)

---

## Implementation Phases

### Phase 1: Critical (Do Immediately)
1. ✅ **Timezone-aware datetime** (30 min) - Security issue
2. ✅ **Database session cleanup** (1 hour) - Memory leak issue

### Phase 2: High Priority (Do Soon)
3. ✅ **Logging infrastructure** (2-3 hours) - Production observability
4. ✅ **Test suite foundation** (4-6 hours) - Regression prevention

### Phase 3: Quality Improvements (Do When Time Permits)
5. ✅ **Centralized configuration** (1-2 hours) - Maintainability
6. ✅ **Typing handler documentation** (5 min) - Code clarity

---

## Testing Strategy

After each fix:
- ✅ Verify existing functionality still works
- ✅ Run new tests (once test suite exists)
- ✅ Manual testing of affected features
- ✅ Check logs for errors/warnings
- ✅ Monitor database connections

---

## Success Criteria

- [ ] All `datetime.utcnow()` replaced with timezone-aware version
- [ ] Database sessions properly cleaned up (WebSocket handler at minimum)
- [ ] No `print()` statements in production code
- [ ] Logging configured with file rotation
- [ ] Configuration centralized in `config.sh`
- [ ] Magic numbers moved to `Config` class
- [ ] Typing handler has clear documentation
- [ ] Test suite with >70% coverage of critical paths
- [ ] Tests run in CI (if applicable)
- [ ] No regressions in functionality

---

## Notes

### Issue Deferred: File Upload Security (LOW PRIORITY)

**Reason:** Application designed for self-hosted, local, single-user deployment.

**If deployment model changes**, address:
- MIME type validation (not just extension)
- Virus/malware scanning
- Rate limiting
- Content inspection

For current use case, risk is acceptable.

---

## Estimated Total Effort

- **Critical issues:** 1.5 hours
- **High priority:** 6-9 hours  
- **Quality improvements:** 2 hours

**Total:** 9.5-12.5 hours

---

## Dependencies

- Phase 1 can be done independently
- Phase 2 (logging) should be done before extensive testing
- Phase 3 can be done in any order
- Test suite should be built incrementally alongside fixes
