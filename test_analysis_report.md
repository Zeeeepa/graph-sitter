# Test Suite Analysis Report
==================================================

## 📊 Test Suite Metrics
- Total test files: 404
- Skipped tests: 128
- XFail tests: 30
- Platform-specific skips: 8

## ⚠️ Skipped Tests Analysis
Total skipped: 168

### Top skip reasons:
- No reason provided: 84
- No Autocommit: 15
- macOS is case-insensitive: 8
- Blocked on CG-11949: 6
- wip: 5
- TODO: Github tests: 4
- Log propagate is off: 3
- CG-9463: Fix resolved types to be start byte aware: 3
- TODO: 2
- CG-8883: Parenthesized expressions not implemented yet: 2

## ⚡ Performance Issues
Total issues found: 4

## 📈 Coverage Gaps
Potentially untested files: 531

## 🎯 Recommendations

1. **High Priority**: Address skipped tests - over 10 tests are currently skipped
3. **Medium Priority**: Improve test coverage - many source files lack corresponding tests
4. **Low Priority**: Remove duplicate tests to reduce maintenance overhead