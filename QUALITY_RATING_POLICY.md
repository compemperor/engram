# Quality Rating Policy

**Version:** 1.0  
**Created:** 2026-02-02  
**Purpose:** Standardize source quality evaluation across all AI agents using Engram

---

## The Problem

AI agents (including ourselves) can unconsciously inflate quality ratings to ensure interesting information gets saved. This defeats the purpose of quality gates and leads to memory pollution.

**This policy establishes objective criteria for rating source quality.**

---

## Quality Scale (1-10)

### 🔴 Low Quality (1-5)
**Save threshold:** No auto-save  
**Use:** Scratch notes, leads, unverified tips

**Characteristics:**
- Single source, unverified
- Social media posts (X/Twitter, Reddit, etc.)
- Anonymous sources
- No corroboration
- Speculation or rumors
- Outdated information (>2 years in tech/finance)

**Examples:**
- Single tweet claiming something
- Reddit comment without sources
- Blog post with no citations
- "I heard that..." statements

---

### 🟡 Medium Quality (6-7)
**Save threshold:** No auto-save  
**Use:** Useful reference, needs verification

**Characteristics:**
- One credible source OR two weak sources
- Secondary sources (analysis, commentary)
- Tech blogs with reputation
- Company blogs (biased but factual)
- Breaking news (not yet verified)
- Recent information (<6 months)

**Examples:**
- TechCrunch article citing unnamed sources
- Company announcement on their own blog
- Analyst report from known firm
- News article with single source

---

### 🟢 High Quality (8-10)
**Save threshold:** Auto-save to permanent memory  
**Use:** Teach-worthy insights, reliable facts

**Characteristics:**
- **8:** TWO+ independent sources agree
- **9:** Primary source + independent verification
- **10:** Peer-reviewed or official announcement + multiple confirmations

**Required for 8+:**
- Multiple independent sources (Two-Source Rule)
- Primary sources preferred over secondary
- Current information (<1 year for tech/finance)
- No conflicts of interest
- Verifiable facts, not opinions

**Examples (Quality 8):**
- Reuters + Bloomberg both report same data
- Company SEC filing + analyst confirmation
- Academic paper + replication study

**Examples (Quality 9):**
- Official press release + media verification
- Government data + independent analysis
- Product launch + technical specifications

**Examples (Quality 10):**
- Peer-reviewed journal article + meta-analysis
- Multiple independent research teams confirm
- Official statistics from authoritative body

---

## Source Evaluation Framework

### CRAAP Test (Academic Standard)

Use these five criteria for EVERY source:

**C - Currency (Timeliness)**
- When was it published?
- Is it current enough for your topic?
- Tech/finance: <1 year preferred
- Science: <5 years
- Historical: date less important

**R - Relevance (Importance)**
- Does it directly address your question?
- Is it at the appropriate level?
- Would you cite this in a report?

**A - Authority (Credibility)**
- Who is the author/publisher?
- What are their credentials?
- Is it peer-reviewed?
- Are there conflicts of interest?

**A - Accuracy (Reliability)**
- Can you verify the information elsewhere?
- Are sources cited?
- Is it factual or opinion?
- Has it been reviewed/edited?

**P - Purpose (Intent)**
- Why does this information exist?
- Is it to inform, persuade, sell, entertain?
- Is there bias?
- Is it satire/parody?

---

## Source Hierarchy

**Priority order (highest to lowest):**

1. **Primary Sources** (Quality 9-10 if verified)
   - Original research
   - Official announcements
   - Direct data
   - First-hand accounts
   - Government statistics
   - Company SEC filings

2. **Secondary Sources** (Quality 7-8 if multiple)
   - Peer-reviewed analysis
   - Expert commentary
   - Investigative journalism
   - Meta-analyses
   - Synthesis of primary sources

3. **Tertiary Sources** (Quality 5-7)
   - Encyclopedias
   - Textbooks
   - Summaries
   - Aggregators
   - News aggregators

4. **Social Media** (Quality 1-6, MAX 6 without verification)
   - Treat as tips/signals only
   - MIT Study: False news spreads faster on Twitter
   - Require external corroboration
   - Can be quality 6 if from verified expert + on-topic

---

## The Two-Source Rule

**For quality 8+, you MUST have:**

✅ **Two INDEPENDENT sources** that corroborate the claim

**Independent means:**
- Different organizations
- Different authors
- Different data sources
- Not citing each other
- No shared conflicts of interest

**Examples:**

❌ **NOT independent:**
- TechCrunch article + The Verge article both citing same source
- Tweet + retweet
- News article + company press release (source cited)

✅ **Independent:**
- Bloomberg + Reuters independently report same numbers
- Academic study + replication by different team
- Government data + industry association data match

---

## Social Media Special Rules

**Twitter/X, Reddit, LinkedIn, etc.:**

**Maximum quality: 6** (without external verification)

**Treat as:**
- Signals, not facts
- Tips for further research
- Sentiment indicators
- Lead generation

**Never treat as:**
- Verified facts
- Reliable sources
- Evidence for claims rated 8+

**Exception:** Verified expert posting on-topic research can be quality 6, but still requires external corroboration for 8+.

---

## Breaking News vs. Established Facts

**Breaking News (<24 hours):**
- Maximum quality: 7
- Reason: Not enough time for verification
- Downgrade until independent confirmation

**Established Facts (>1 week):**
- Can be quality 8+ if verified
- Multiple sources had time to corroborate
- Retractions would have been published

**Example:**
- Company announces product → Quality 7 (single source)
- One week later, analysts confirm specs → Quality 8 (verified)

---

## Rating Checklist

**Before rating 8 or higher, verify:**

- [ ] Do I have TWO+ independent sources?
- [ ] Are the sources credible (CRAAP test)?
- [ ] Is the information current enough?
- [ ] Have I checked for conflicts of interest?
- [ ] Is this a primary or verified secondary source?
- [ ] Have I downgraded social media appropriately?
- [ ] Am I being honest, or inflating to save?

**If you can't check all boxes → quality is 7 or lower.**

---

## Common Rating Mistakes

### ❌ Inflating to Save
**Problem:** "This is interesting, I'll call it quality 8 so it saves"  
**Fix:** Be honest. Quality 6-7 can still be useful, just needs verification.

### ❌ Single Source = High Quality
**Problem:** "This is from a good source, quality 9!"  
**Fix:** Even good sources need corroboration for 8+.

### ❌ Social Media Overrating
**Problem:** "This tweet is from an expert, quality 8!"  
**Fix:** Social media MAX 6 without external verification.

### ❌ Confusing Interesting with Quality
**Problem:** "This is fascinating, quality 9!"  
**Fix:** Interesting ≠ reliable. Evaluate objectively.

### ❌ Ignoring Recency
**Problem:** "This 2020 article is quality 9!"  
**Fix:** Tech/finance info >2 years old should be downgraded.

---

## Decision Tree

```
START: You found information

↓
Is it from social media only?
  YES → MAX quality 6
  NO → Continue

↓
How many independent sources?
  ONE → MAX quality 7
  TWO+ → Continue to 8+

↓
Is it a primary source?
  YES → Quality 9 (if verified)
  NO → Continue

↓
Is it peer-reviewed or official?
  YES → Quality 10 (if multiple confirmations)
  NO → Quality 8

↓
Apply CRAAP test
  PASS → Keep rating
  FAIL → Downgrade to 5-6

↓
Check recency
  Current → Keep rating
  Outdated → Downgrade by 1-2
```

---

## Examples Applied

### Example 1: Tech News
**Source:** Single tweet claiming "DeepSeek has breakthrough training method"

**Evaluation:**
- Social media (MAX 6) ✓
- Single source ✓
- Unverified ✓

**Rating:** 4-5 (tip, needs verification)

---

### Example 2: Tech News (Verified)
**Sources:**
1. ClawSearch tech results mention DeepSeek
2. Multiple tweets reference same method
3. Tech blogs discussing it

**Evaluation:**
- Multiple sources ✓
- Mix of social + search ✓
- Still no official source ✗

**Rating:** 7 (likely true, worth noting, but not gold standard)

---

### Example 3: Market Data
**Source:** Single X post claiming "Humanoid robots: $2B → $4B market"

**Evaluation:**
- Social media (MAX 6) ✓
- Single user (@GlobalCloser) ✓
- No linked sources ✓

**Rating:** 5 (interesting claim, needs verification)

---

### Example 4: Market Data (Verified)
**Sources:**
1. Goldman Sachs research report
2. Morgan Stanley forecast
3. Industry association data

**Evaluation:**
- Three independent sources ✓
- Primary sources (research reports) ✓
- Recent (<1 year) ✓
- Credible institutions ✓

**Rating:** 9 (highly reliable, teach-worthy)

---

### Example 5: Company Announcement
**Source:** "Neuralink OneLink 13 Pro" tweet

**Evaluation:**
- Social media only ✓
- No official Neuralink announcement ✗
- Sounds like satire ✗

**Rating:** 2-3 (likely fake, do not save)

---

### Example 6: Official Announcement (Verified)
**Sources:**
1. Company press release (official)
2. Reuters reports it
3. Product page live

**Evaluation:**
- Primary source (company) ✓
- Independent confirmation (Reuters) ✓
- Verifiable (product page) ✓

**Rating:** 9 (verified official announcement)

---

## Policy Enforcement

**For AI agents using Engram:**

1. **Read this policy** before every learning session
2. **Apply CRAAP test** to each source
3. **Check Two-Source Rule** for anything rated 8+
4. **Document reasoning** in note metadata when rating 8+
5. **Be conservative** - when in doubt, rate lower

**For humans reviewing agent work:**

- Spot-check quality ratings periodically
- Challenge 8+ ratings: "Show me your two sources"
- Downgrade violations: Social media rated 8+ → reject
- Provide feedback: Help agents calibrate

---

## Revision History

**v1.0 (2026-02-02):**
- Initial policy based on learning session
- Research sources: CRAAP test, journalism standards, MIT social media study
- Established 1-10 scale with 8+ threshold
- Two-Source Rule for high-quality ratings
- Social media maximum rating of 6

---

## References

- CRAAP Test (Sarah Blakeslee, CSU Chico)
- Two-Source Rule (investigative journalism standard)
- MIT Study: False news spreads faster on Twitter (2018)
- Primary/Secondary/Tertiary source hierarchy (academic standard)
- Peer review standards (scientific publishing)

---

**Remember:** The goal is memory quality, not quantity. Be ruthless with ratings. Only gold gets saved.

🦀
