Here is the markdown content ready to be saved as `SESSION_CHANGES.md`:

```markdown
# Session Changes - Genesis API Integration

**Date:** June 17, 2026  
**Summary:** Adapted the agentic-ui project to work with the Genesis Completions API instead of the OpenAI Assistants API pattern.

---

## Overview

The original code assumed Genesis used the OpenAI Assistants API pattern (`/threads`, `/messages`, `/runs`), but the actual Genesis API uses a simpler **Completions endpoint** (`/completions`) with synchronous responses.

---

## Files Modified

### 1. [agent/genesis_client.py](cci:7://file:///c:/Users/e394102/Downloads/agentic-ui/agent/genesis_client.py:0:0-0:0)

**Original Issue:** Code tried to use `/threads` endpoint which returned 501 Not Implemented.

**Changes Made:**

#### a) Updated module docstring
- Changed from "Assistants API" to "Completions API" description
- Documented that the API is stateless and requires client-side context management

#### b) Rewrote [GenesisClient.__init__()](cci:1://file:///c:/Users/e394102/Downloads/agentic-ui/agent/genesis_client.py:36:4-53:51) (lines 37-54)
```python
# BEFORE: Required assistant_id and poll_seconds
def __init__(self, api_key, assistant_id, base_url, *, poll_seconds=60)

# AFTER: Uses model name instead, with timeout
def __init__(self, api_key, model, base_url, *, timeout=30.0)
```
- Added `LLM_MODEL` support (defaults to `"openai/gpt-oss-120b"`)
- Extracts model name without provider prefix (`openai/gpt-oss-120b` → `gpt-oss-120b`)
- Removed `assistant_id` requirement
- Changed `poll_seconds` to `timeout`

#### c) Simplified [start_thread()](cci:1://file:///c:/Users/e394102/Downloads/agentic-ui/agent/genesis_client.py:59:4-62:29) (lines 60-63)
```python
# BEFORE: POST to /threads endpoint
# AFTER: No-op (kept for interface compatibility)
def start_thread(self) -> str:
    self.thread_id = "completions-session"
    return self.thread_id
```

#### d) Completely rewrote [ask()](cci:1://file:///c:/Users/e394102/Downloads/agentic-ui/agent/genesis_client.py:64:4-109:103) method (lines 65-110)
```python
# BEFORE: Multi-step flow (POST messages → POST runs → poll status → GET messages)
# AFTER: Single synchronous POST to /completions
```
- Single POST to `/completions` endpoint
- Payload: `{"model": "gpt-oss-120b", "prompt": "...", "max_tokens": 800, "temperature": 0.3, "stop": [...]}`
- Added stop sequences to prevent reasoning loops: `["\n\n{", "```\n{", "USER QUESTION:", "\n\nWe need", "\n\nThe user"]`
- Parse OpenAI-style JSON response structure: `response.json()["choices"][0]["text"]`
- Strip reasoning text before JSON (post-processing to remove any text before `{`)
- Lower temperature (0.3) to reduce creative "thinking out loud" behavior

---

### 2. [server/genesis_app.py](cci:7://file:///c:/Users/e394102/Downloads/agentic-ui/server/genesis_app.py:0:0-0:0)

**Changes Made:**

#### a) Updated module docstring (lines 1-19)
- Changed instructions to reflect completions API usage
- Updated example to show `LLM_API_KEY` and `LLM_MODEL` instead of `PM_ASSISTANT_ID`

#### b) Fixed mock mode detection (line 48)
```python
# BEFORE: Required both LLM_API_KEY and PM_ASSISTANT_ID
_USE_MOCK = os.getenv("GENESIS_MOCK") == "1" or not (os.getenv("LLM_API_KEY") and os.getenv("PM_ASSISTANT_ID"))

# AFTER: Only requires LLM_API_KEY (PM_ASSISTANT_ID not needed for completions API)
_USE_MOCK = os.getenv("GENESIS_MOCK") == "1" or not os.getenv("LLM_API_KEY")
```

#### c) Fixed response structure (lines 83-91)
```python
# BEFORE: Included context_used field
return {
    "text": result.text,
    "payloads": result.payloads,
    "artifacts": result.artifacts,
    "context_used": result.context_used,
}

# AFTER: Removed context_used
return {
    "text": result.text,
    "payloads": result.payloads,
    "artifacts": result.artifacts,
}
```

---

### 3. [.env.example](cci:7://file:///c:/Users/e394102/Downloads/agentic-ui/.env.example:0:0-0:0)

**Changes Made:**

#### Added LLM_MODEL requirement (lines 1-16)
```bash
# BEFORE:
LLM_API_KEY=""
PM_ASSISTANT_ID=""
GENESIS_BASE_URL="https://api.ai.us.lmco.com/v1"

# AFTER:
LLM_API_KEY=""                       # your internal Genesis API key (Bearer token)
LLM_MODEL="openai/gpt-oss-120b"      # model name (provider/model format)
GENESIS_BASE_URL="https://api.ai.us.lmco.com/v1"
PM_ASSISTANT_ID=""                   # Optional: not used by completions API
```

---

### 4. [agent/genesis_agent.py](cci:7://file:///c:/Users/e394102/Downloads/agentic-ui/agent/genesis_agent.py:0:0-0:0)

**Changes Made:**

#### a) Strengthened system instruction (lines 60-90)
**Key changes:**
- Added explicit "Output ONLY JSON" instructions
- Listed all valid userIntent values explicitly
- Added default program "P-117" to use when not specified
- Emphasized starting response with `{` immediately

**New critical rules:**
- Output ONLY JSON - NO explanations, NO reasoning, NO thinking, NO prose
- Start your response immediately with `{`
- End after the closing `}`

**Valid userIntent values:** `trend_analysis, comparison, status_summary, distribution, ranking, schedule, root_cause, detail_lookup`

#### b) Improved JSON extraction (lines 101-139)
```python
# BEFORE: Simple find/rfind approach
def _extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start : end + 1])

# AFTER: Brace-counting to find first complete JSON object
```
- Uses depth tracking to find matching closing brace
- Handles nested JSON structures properly
- Stops after first complete object

#### c) Added validation error handling (lines 182-200)
```python
# BEFORE: Validation errors crashed
payload = _adapter.validate_python(raw_payload)

# AFTER: Falls back to table on errors
try:
    payload = _adapter.validate_python(raw_payload)
except Exception as e:
    # Fall back to table with error message
```

---

## Configuration Changes Required

### Your [.env](cci:7://file:///c:/Users/e394102/Downloads/agentic-ui/.env:0:0-0:0) file should include:

```bash
LLM_API_KEY=eyJhbGciOiJSUzI1NiIsImtpZCI6InVCWDFsbzJjY2gzbkp5R1A5RTNlY2lhV29mQ2RWcFJacWkyWjZNUG9fdGciLCJ0eXAiOiJKV1QifQ...
LLM_MODEL=openai/gpt-oss-120b
GENESIS_BASE_URL=https://api.ai.us.lmco.com/v1

# For testing with mock mode:
# GENESIS_MOCK=1
```

---

## API Request Format Change

### Before (Assistants API):
```
POST /threads → thread_id
POST /threads/{id}/messages
POST /threads/{id}/runs
Poll GET /threads/{id}/runs/{run_id}
GET /threads/{id}/messages
```

### After (Completions API):
```
POST /completions
Body: {
  "model": "gpt-oss-120b",
  "prompt": "<context>",
  "max_tokens": 800,
  "temperature": 0.3,
  "stop": ["\n\n{", "```\n{", "USER QUESTION:", "\n\nWe need", "\n\nThe user"]
}
```

---

## Actual Behavior in Testing

### Test Results (5 Canned Prompts)

#### ❌ **"Show CPI trend for the last six months"**
**Expected:** Line chart showing CPI data  
**Actual:** No response displayed in chat (silent failure)

#### ❌ **"Show top risks by likelihood and impact"**
**Expected:** Risk matrix visualization  
**Actual:** No response displayed in chat (silent failure)

#### ❌ **"Summarize program health"**
**Expected:** KPI cards with health metrics  
**Actual:** Model outputs reasoning text instead of JSON:
```
We need to produce JSON action. The user wants "Summarize program health." 
That corresponds to KPI card, status_summary. Use get_program_health tool. 
So action: fetch_data with tool get_program_health, args program P-117, 
then component kpi_card, title maybe "Program Health Summary", userIntent 
status_summary, fields maybe none? The fields may not be needed. But spec expects fields with x and y 
for chart; for kpi_card maybe not needed. Could leave empty object. Provide 
summary and explanation. Let's craft.
```

#### ✅ **"Compare SPI across control accounts"** - ONLY WORKING PROMPT
**Expected:** Bar chart comparing SPI across accounts  
**Actual:** **Chart rendered successfully!**
```
Shows SPI variation across control accounts
SPI by Control Account
[Bar chart displaying data]
Highlights which accounts are over/under performing
Source: EVMS MCP
```

#### ❌ **Follow-up questions after successful chart**
**Examples tested:**
- "Why did March dip?" → **No response (silent failure)**
- "help me understand the SPI trend better" → **Returns single "?" character**
- "can you help me understand the plot better" → **Returns single "?" character**

---

## Known Issues - Detailed Analysis

### Issues Summary

| Issue | Status | Impact |
|-------|--------|--------|
| Reasoning text instead of JSON | ❌ Critical | 3 of 5 prompts fail |
| Silent failures | ❌ Critical | 2 of 5 prompts produce no output |
| Follow-up questions broken | ❌ Critical | Returns "?" after successful chart |
| Only 1 prompt works | ⚠️ Major | 20% success rate on canned prompts |

### Issue #1: Model Generates Reasoning Instead of JSON

**Affected Prompts:**
- "Summarize program health"

**Symptoms:**
- Model outputs its internal reasoning process
- No JSON action object generated
- Agent loop can't parse the response
- Results in display of raw reasoning text to user

**Example Output:**
```
We need to produce JSON action. The user wants "Summarize program health." 
That corresponds to KPI card, status_summary...
```

**Attempted Fixes:**
- ✅ Added explicit "Output ONLY JSON" instructions
- ✅ Added stop sequences: `["\n\nWe need", "\n\nThe user"]`
- ✅ Lowered temperature to 0.3
- ✅ Post-processing to strip text before `{`
- ❌ **Still fails** - Model bypasses all constraints

---

### Issue #2: Silent Failures

**Affected Prompts:**
- "Show CPI trend for the last six months"
- "Show top risks by likelihood and impact"

**Symptoms:**
- HTTP 200 OK response
- No error in logs
- No content displayed in chat
- User sees empty analyst response

**Possible Causes:**
1. Model generates invalid JSON that fails parsing silently
2. JSON parsing extracts empty object
3. Response validation fails but doesn't throw error
4. Frontend receives empty payload and displays nothing

**Not Yet Debugged:** Need to add verbose logging to see what the model actually returns for these prompts.

---

### Issue #3: Follow-up Questions Return "?"

**Affected Scenario:**
- After "Compare SPI across control accounts" successfully renders chart
- Any follow-up question fails

**Examples:**
```
User: "Why did March dip?"
Analyst: (no response)

User: "help me understand the SPI trend better"
Analyst: ?

User: "can you help me understand the plot better"
Analyst: ?
```

**Possible Causes:**
1. Artifact context not being properly stored/retrieved
2. Model receiving corrupted or incomplete prompt with artifact digest
3. Model generating response shorter than minimum viable JSON
4. JSON extraction failing on minimal response and returning "?" as fallback
5. Stop sequences triggering too early on follow‑up questions

**Hypothesis:** The agent loop's [_extract_json()](cci:1://file:///c:/Users/e394102/Downloads/agentic-ui/agent/genesis_agent.py:110:0-148:71) might be returning `"?"` when it can't parse anything, or the frontend displays `"?"` when it receives an error response.

---

### Issue #4: Why Only "Compare SPI" Works

**Working Prompt Analysis:**
```
"Compare SPI across control accounts"
```

**Success Pattern:**
- Clear intent: comparison
- Specific data: SPI → bar_chart
- Simple fields: `{"x": "account", "y": "spi"}`

**Hypothesis:** This prompt's structure and simplicity makes it easier for the model to generate valid JSON without overthinking.

**Other prompts might fail because:**
1. **"Show CPI trend"** – “trend” may trigger time‑series reasoning loops
2. **"Show top risks"** – “risks” with likelihood×impact may confuse field mapping
3. **"Summarize"** – Abstract intent triggers reasoning about what to summarize
4. **Follow‑ups** – Require artifact context which might be malformed

---

## Root Cause Analysis

### Primary Issue: Model Instruction Following

The Genesis LLM (`gpt-oss-120b`) appears to be:
1. **Trained for conversational reasoning** rather than structured output  
2. **Not respecting stop sequences** consistently  
3. **Interpreting “Output JSON” as a suggestion** rather than a hard constraint  
4. **Thinking through the problem** before answering (chain‑of‑thought behavior)

### Evidence
- Direct reasoning text in output: “We need to produce JSON action…”
- Inconsistent JSON generation (1 of 5 works)
- “?” responses suggest JSON parsing failures
- Model doesn’t start response with `{` despite explicit instruction

---

## Recommended Next Steps

### Immediate Debugging
1. **Add verbose logging** to capture raw model responses for all 5 prompts
2. **Log JSON parsing failures** with the exact text that failed
3. **Log frontend payloads** to see what reaches the UI
4. **Add error boundaries** to catch and display parsing errors

### Short‑term Fixes to Try
1. **Few‑shot prompting:** Add 2‑3 example Q&A pairs showing correct JSON output  
2. **Prefix forcing:** Pre‑pend `"{\"action\":\"` to force a JSON start  
3. **Increase `max_tokens`:** Try 1200 to see if the model completes JSON before cutoff  
4. **Test a different model:** If another Genesis model is available  
5. **Check for a “structured output” mode** in the API (e.g., schema constraints)

### Long‑term Solutions
1. **Use a model fine‑tuned for structured output** (rather than `gpt-oss-120b`)  
2. **Add a validation layer** that retries with stricter prompts on failure  
3. **Implement a “repair” step** that fixes malformed JSON automatically  
4. **Fall back to mock mode** for demos until live‑API issues are resolved  
5. **Consider a different API pattern** if available (e.g., function calling)

---

## Alternative Approach: Use Mock Mode

Since only 1 of 5 prompts works, **mock mode is currently more reliable** for demonstrations:

```bash
# In .env
GENESIS_MOCK=1
```

Mock mode provides:
- ✅ 100 % success rate on all canned prompts  
- ✅ Charts render correctly  
- ✅ Follow‑up questions work (e.g., “Why did March dip?”)  
- ✅ Artifact awareness functions properly  
- ❌ Limited to pre‑programmed responses

**Recommendation:** Use mock mode for demos/testing until the live API issues are resolved.

---

## Files Changed Summary

1. **[agent/genesis_client.py](cci:7://file:///c:/Users/e394102/Downloads/agentic-ui/agent/genesis_client.py:0:0-0:0)** – Rewrite for completions endpoint  
2. **[server/genesis_app.py](cci:7://file:///c:/Users/e394102/Downloads/agentic-ui/server/genesis_app.py:0:0-0:0)** – Fixed mock detection and response  
3. **[.env.example](cci:7://file:///c:/Users/e394102/Downloads/agentic-ui/.env.example:0:0-0:0)** – Added `LLM_MODEL`  
4. **[agent/genesis_agent.py](cci:7://file:///c:/Users/e394102/Downloads/agentic-ui/agent/genesis_agent.py:0:0-0:0)** – Better instructions, JSON extraction, error handling  

---

## Testing Commands

```bash
# Test in mock mode (RECOMMENDED – works reliably)
# Add to .env: GENESIS_MOCK=1
npm run dev:genesis

# Test with live API (currently only ~20 % success rate)
# Set LLM_API_KEY and LLM_MODEL in .env
npm run dev:genesis

# Open in browser
http://localhost:5173/genesis.html
```

---

**End of session changes document.**