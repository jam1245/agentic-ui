"""
Fake HR data injected into the system prompt when DEVELOPER_MODE = True.
"""

DEV_CONTEXT = """
---
## DEVELOPER TEST CONTEXT — Logged-in user: Quinn

You have full access to Quinn's HR data. Use it to respond to any request about goals, feedback,
assessments, check-ins, awards, or performance data. When the user asks about "my" anything,
refer to Quinn's data below.

---

### Employee Profile
- **Name:** Quinn
- **Title:** Software Engineer L4
- **Team:** Platform Engineering — Developer Experience
- **Manager:** Sarah Kim (Director of Engineering)
- **Tenure:** 10 years, 3 months (joined 2016)
- **Location:** Austin, TX
- **Review Cycle:** Annual (closes Dec 15), Mid-Year (closes Jun 30)

---

### Alex's 2026 Goals (current year)

1. **Launch DX Observability Dashboard**
   - Owner: Quinn
   - Status: on_track
   - Start: 2026-01-01
   - Target: 2026-06-30
   - Progress: 55%
   - Key Results:
     - [x] Instrument top 5 internal services with OpenTelemetry
     - [x] Build v1 dashboard in Grafana
     - [ ] Onboard 3 teams as active users
     - [ ] Achieve <5 min mean time to detection on P1s

2. **Reduce CI Build Times by 40%**
   - Owner: Quinn
   - Status: at_risk
   - Start: 2026-01-01
   - Target: 2026-09-30
   - Progress: 30%
   - Key Results:
     - [x] Audit and profile all CI pipelines
     - [ ] Implement remote caching for monorepo builds
     - [ ] Cut average build time from 14 min to 8 min
     - [ ] Document caching best practices for all teams

3. **Grow as a Technical Mentor**
   - Owner: Quinn
   - Status: on_track
   - Start: 2026-01-01
   - Target: 2026-12-31
   - Progress: 40%
   - Key Results:
     - [x] Formally mentor 2 junior engineers
     - [ ] Lead 4 internal tech talks (2 of 4 done)
     - [ ] Co-author 1 engineering blog post

4. **Complete L4 → L5 Promotion Readiness Plan**
   - Owner: Quinn
   - Status: draft
   - Start: 2026-04-01
   - Target: 2026-11-30
   - Progress: 10%
   - Key Results:
     - [ ] Agree on promotion criteria with Sarah
     - [ ] Deliver 1 cross-team impact project
     - [ ] Collect 5+ strong peer endorsements

---

### Alex's 2025 Goals (prior year — all closed)

1. **Migrate Legacy Auth Service to OAuth 2.0** — Complete ✓ (100%)
2. **Lead Q2 On-Call Rotation Redesign** — Complete ✓ (100%)
3. **Build Internal Developer CLI (devx-cli)** — Complete ✓ (85% — shipped MVP, full v1 slipped to 2026)

---

### Sarah Kim's Goals (Alex's manager — 2026)

1. **Scale Platform Engineering team from 8 to 12 engineers** — on_track, Target: 2026-08-31
2. **Achieve 99.9% platform uptime SLA across all services** — at_risk, Target: 2026-12-31

---

### Feedback Alex Received (2025 Annual Cycle — 4 reviewers)

**From: Jordan Lee (Senior Engineer, same team)**
- Date: 2025-11-18
- Competency: Technical Execution
- Sentiment: positive
- Strengths: "Alex's work on the auth migration was methodical and risk-aware. Every PR was well-documented and he proactively identified two edge cases that would have caused prod incidents."
- Development: "Alex could delegate more — he tends to keep complex tasks to himself rather than using them as teaching moments for newer engineers."

**From: Priya Nair (Product Manager, DX team)**
- Date: 2025-11-20
- Competency: Collaboration
- Sentiment: positive
- Strengths: "One of the best engineers I've partnered with. Alex translates technical complexity into business impact naturally and always follows through on commitments."
- Development: "Could push back earlier when scope creep happens — sometimes lets features grow without flagging the trade-offs."

**From: Marcus Webb (Junior Engineer, mentee)**
- Date: 2025-11-22
- Competency: Mentorship & Growth
- Sentiment: positive
- Strengths: "Alex genuinely invests in people. He made himself available every week and never made me feel like a burden. Huge reason I grew this year."
- Development: "Sometimes moves fast in explanations — slowing down would help on complex topics."

**From: Tara Simmons (Engineering Manager, adjacent team) — Anonymous**
- Date: 2025-11-25
- Competency: Leadership
- Sentiment: constructive
- Strengths: "Strong technical credibility and respected by peers."
- Development: "Alex's impact is mostly felt within his team. To move to L5 he needs to demonstrate broader org-level influence — driving cross-team initiatives, not just participating in them."

**Feedback themes (strengths):** Technical rigor, Reliability, Collaboration, Mentorship, Communication
**Feedback themes (development):** Broader scope / org influence, Delegation, Scope management

---

### Feedback Alex Gave (2025 Annual Cycle)

**To: Marcus Webb** — Strengths: strong growth mindset and coachability. Dev area: needs to build more confidence in code reviews.
**To: Priya Nair** — Strengths: exceptional at holding context across many workstreams. Dev area: could prototype ideas earlier before full spec.

---

### Alex's 2025 Self-Assessment (Annual Review)

**Accomplishments:**
"This year I'm most proud of leading the OAuth 2.0 migration end to end. The project touched 14 services, required coordination with 6 teams, and shipped with zero production incidents — something I attribute to thorough runbook preparation and proactive stakeholder communication. I also launched devx-cli which is now used daily by ~40 engineers and has reduced common setup tasks from 20 minutes to under 2 minutes."

**Strengths:**
"I've grown significantly in my ability to drive projects that require cross-functional alignment. I've also become a more intentional mentor — moving from ad-hoc help to structured 1:1s with clear growth plans for Marcus and Jamie."

**Development Areas:**
"I need to work on operating at a broader scope. Most of my impact has been deep within my team's domain. In 2026 I want to take on at least one initiative that affects the broader engineering org. I also want to improve at saying 'no' earlier when feature requests would add technical debt."

**Goals for 2026:**
"Launch the DX Observability Dashboard and position it as a platform-wide capability. Reduce CI build times significantly — this has been a consistent pain point across teams. Achieve promotion readiness for L5 by demonstrating org-wide impact."

---

### Sarah's Closeout of Alex (2025 Annual Review — written by Sarah Kim)

**Performance Summary:**
"Alex had a strong 2025. The OAuth migration was his most visible project and he executed it with the care and precision I've come to expect. His technical bar is consistently high and he's become a trusted resource across teams."

**Rating:** Exceeds Expectations (4 / 5 tiers)

**Strengths:**
"Alex's ability to deliver complex, high-stakes work independently is his clearest differentiator. He's also made real strides in mentorship this year — Marcus's growth is a direct reflection of Alex's investment."

**Development Areas:**
"The main thing holding Alex back from L5 is scope. He needs to show that he can identify and drive problems that span multiple teams or systems — not just execute within his own domain. I want to see him propose and own a platform-wide initiative in H1 2026."

**Manager Rating Justification:**
"Exceeds Expectations reflects both the quality of Alex's delivery and the positive influence he's had on the team. The gap to Distinguished is the org-level impact bar he hasn't yet crossed."

---

### Awards

Quinn **started at the company in 2016**. Award history runs **2016 through 2026** (11 years). Never say 2016 was "not yet at company" — that year is Quinn's start year.

| Year | Count | Notes |
|------|-------|-------|
| 2016 | 5 | Start year at company; onboarding kudos, on-call assists |
| 2017 | 7 | Steady peer recognition |
| 2018 | 9 | Hackathon participation, team shoutouts |
| 2019 | 11 | Reliability and incident response awards |
| 2020 | 12 | Remote-work collaboration badges |
| 2021 | 10 | Strong delivery year; peer recognition |
| 2022 | 14 | Hackathon winner; team-wide shoutouts |
| 2023 | 18 | Team Excellence Award; DX CLI launch recognition |
| 2024 | 20 | Innovation Award; Collaboration Award; most nominated on Platform |
| 2025 | 17 | Engineering Excellence Award (OAuth migration); peer kudos |
| 2026 | 6 | Mid-year to date |

**Chart data (display_plotly_chart):** x_labels `["2016","2017","2018","2019","2020","2021","2022","2023","2024","2025","2026"]`, y_values `[5,7,9,11,12,10,14,18,20,17,6]`, title "Awards Received Over Time".

- **Total awards (2016–2026):** 129

**Most recent award detail — Q3 2025 — Engineering Excellence Award**
- Given by: Sarah Kim
- Date: 2025-09-15
- Citation: "Awarded to Quinn for the flawless execution of the OAuth 2.0 migration, which eliminated a critical security risk while achieving zero downtime. The level of preparation, communication, and cross-team coordination was exemplary."
- Badge: trophy

---

### Action Items from Last Check-In (April 2, 2026 with Sarah Kim)

1. [ ] Draft scope doc for CI caching project — due 2026-04-16
2. [x] Set up bi-weekly mentorship sessions with Jamie Park — completed
3. [ ] Identify one cross-team initiative to propose for H1 — due 2026-05-01
4. [ ] Share draft DX dashboard with Platform team leads — due 2026-04-30
5. [x] Submit Q1 self-reflection doc — completed

---

### Upcoming Deadlines

- **Mid-Year Self-Assessment due** — 2026-06-25 (required)
- **DX Dashboard v1 milestone** — 2026-06-30 (goal target)
- **CI Build Time reduction checkpoint** — 2026-07-15 (internal)
- **Annual Promo Readiness conversation with Sarah** — 2026-11-01 (planned)
- **Annual Review window opens** — 2026-11-15

---
"""
