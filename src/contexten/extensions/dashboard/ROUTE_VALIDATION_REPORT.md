============================================================
ROUTE VALIDATION REPORT
============================================================

📊 SUMMARY:
   Total Routes Tested: 8
   Working Routes: 7
   Broken Routes: 1
   Success Rate: 87.5%

🔍 ROUTE DETAILS:

✅ GET /
   Status: 200 (expected 200)
   Response Time: 0.002s
   Content Type: text/html; charset=utf-8
   Content Length: 7659 bytes

✅ GET /health
   Status: 200 (expected 200)
   Response Time: 0.002s
   Content Type: application/json
   Content Length: 79 bytes

✅ GET /api/health
   Status: 200 (expected 200)
   Response Time: 0.002s
   Content Type: application/json
   Content Length: 137 bytes

✅ GET /docs
   Status: 200 (expected 200)
   Response Time: 0.002s
   Content Type: text/html; charset=utf-8
   Content Length: 960 bytes

✅ GET /api/projects
   Status: 200 (expected 200)
   Response Time: 0.002s
   Content Type: application/json
   Content Length: 617 bytes

❌ POST /api/projects
   Status: 200 (expected 422)
   Response Time: 0.002s
   Content Type: application/json
   Content Length: 605 bytes
   Error: Expected 422, got 200

✅ GET /nonexistent
   Status: 404 (expected 404)
   Response Time: 0.002s
   Content Type: application/json
   Content Length: 22 bytes

✅ GET /api/nonexistent
   Status: 404 (expected 404)
   Response Time: 0.002s
   Content Type: application/json
   Content Length: 22 bytes