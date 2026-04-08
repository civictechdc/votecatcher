# Votecatcher Demo Walkthrough

## Overview

This document describes a complete demo walkthrough of Votecatcher's core features. Use this guide to:
- Demonstrate the system to stakeholders
- Test the full workflow end-to-end
- Onboard new users

## Prerequisites

Before starting the demo:

1. **Start the application:**
   ```bash
   # Terminal 1: Backend
   cd backend && uv run python main.py --env local

   # Terminal 2: Frontend
   cd frontend-svelt && bun run dev
   ```

2. **Enable demo mode:**
   ```bash
   # In frontend-svelt/.env
   DEMO_MODE=true
   DEMO_RESET=true
   ```

3. **Verify services are running:**
   - Backend: http://localhost:8080/health
   - Frontend: http://localhost:5173

4. **Reset to clean state:**
   - Navigate to Demo page
   - Click "Reset Demo" → Confirm
   - This clears all data

## Demo Script (5-10 minutes)

### 1. Introduction (30 seconds)

**Say:**
> "Votecatcher automates petition signature verification. What used to take hours of manual comparison now takes minutes. Let me show you how it works."

**Show:**
- Dashboard page with metrics

### 2. Load Demo Data (1 minute)

**Say:**
> "First, let me load a pre-configured demo session with sample petition data from a DC campaign."

**Do:**
1. Navigate to **Demo** in sidebar
2. Click **Load** on "DC Petition Demo"
3. Wait for "Loaded demo session" message

**Show:**
- Success message with voter count and match results

### 3. Review Campaign (30 seconds)

**Say:**
> "The demo created a campaign with sample petitions already processed."

**Do:**
1. Navigate to **Campaigns**
2. Show "DC Demo 2024" campaign

**Show:**
- Campaign list with creation date

### 4. Explore Results (2 minutes)

**Say:**
> "The system has already run OCR and matching. Let's look at the results."

**Do:**
1. Navigate to **Results**
2. Show the results table
3. Filter by confidence level (HIGH, MEDIUM, LOW)
4. Point out the confidence badges

**Show:**
- Results table with columns: Registration Name, Matched Name, Confidence, Address
- Confidence distribution (color-coded badges)
- Pagination controls

**Explain:**
> "Green badges are HIGH confidence - these are very likely correct matches and need minimal review. Yellow are MEDIUM - they need a quick look. Red are LOW confidence and require manual verification."

### 5. View Match Details (1 minute)

**Say:**
> "Let's look at a specific match in detail."

**Do:**
1. Click on a result row (if clickable)
2. Or point out the side-by-side comparison

**Show:**
- OCR-extracted text (what the LLM read from the petition)
- Registered voter data (from the official list)
- Similarity scores

### 6. Export Results (30 seconds)

**Say:**
> "You can export all results for further analysis."

**Do:**
1. Click **Export CSV**
2. Mention the file includes all match data

### 7. Session Management (1 minute)

**Say:**
> "Let's say you need to continue this work tomorrow. You can save your workspace state."

**Do:**
1. Navigate to **Sessions**
2. Click **Save Session**
3. Enter name: "DC Demo - Day 1"
4. Click Save

**Show:**
- Session appears in list
- Load button for restoring

### 8. Reset Demo (30 seconds)

**Say:**
> "Finally, let me clean up by resetting the demo data."

**Do:**
1. Navigate to **Demo**
2. Click **Reset Demo**
3. Confirm in modal
4. Show success message

**Show:**
- Clean state restored

## Key Talking Points

### Technical Highlights

1. **LLM-Based OCR**
   - Uses GPT-4 Vision, Gemini, or Mistral for handwriting recognition
   - Batch API for cost efficiency
   - Async processing with polling

2. **Fuzzy Matching**
   - Hybrid approach: Database pre-filtering + RapidFuzz
   - Handles name variations, misspellings, abbreviations
   - Configurable confidence thresholds

3. **Real-Time Updates**
   - Server-Sent Events for job progress
   - No page refresh needed
   - Live status updates

4. **Accessibility**
   - WCAG 2.2 AA compliant
   - Full keyboard navigation
   - Screen reader compatible

### Cost & Performance

- **Processing time:** ~2-5 minutes for 100 signatures
- **OCR cost:** $0.01-0.03 per signature (depends on provider)
- **Deployment:** Single VPS ($5-20/month)

### Security & Privacy

- No data stored on external servers (except LLM API calls)
- Voter data stays in your database
- Session data is reference-based (not full copies)

## Common Questions

**Q: How accurate is the OCR?**
A: Depends on handwriting quality. For legible signatures, 85-95% accuracy. The fuzzy matching compensates for minor OCR errors.

**Q: Can I use my own voter list format?**
A: Yes, as long as it has the required columns (name, address). The system handles CSV and Excel.

**Q: What about other regions besides DC?**
A: The system is region-agnostic. You just need to configure crop coordinates for your petition format.

**Q: Is my data secure?**
A: Yes. Data stays on your server. LLM providers process images but don't store them (check your provider's policy).

## Demo Checklist

Before presenting:

- [ ] Backend and frontend running
- [ ] Demo mode enabled
- [ ] Demo data loaded
- [ ] Results page populated
- [ ] CSV export works
- [ ] Session save/load works
- [ ] Reset demo works
- [ ] Browser zoom at 100%
- [ ] Good network connection
- [ ] Backup screenshots ready

## Recording the Demo

For video recording:

1. Use screen recording software (OBS, Loom, etc.)
2. Record at 1080p minimum
3. Use a clean browser profile
4. Disable browser notifications
5. Test audio/microphone beforehand
6. Record in one take if possible
7. Add captions for accessibility

**Suggested video structure:**
1. Introduction (10 sec)
2. Load demo data (20 sec)
3. Walk through results (45 sec)
4. Show export feature (15 sec)
5. Session management (20 sec)
6. Conclusion (10 sec)

**Total length:** ~2 minutes

---

## Troubleshooting Demo Issues

**Demo mode not working:**
- Check DEMO_MODE=true in .env
- Restart frontend server
- Clear browser cache

**No results showing:**
- Check backend is running
- Verify database has data
- Check browser console for errors

**Export fails:**
- Check browser popup blocker
- Verify results exist
- Check backend logs

---

**Document Version:** 1.0
**Last Updated:** 2026-03-10
**Author:** Votecatcher Team
