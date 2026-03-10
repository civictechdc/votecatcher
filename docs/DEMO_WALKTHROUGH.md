# Demo Walkthrough Guide

## Overview

This guide walks through a complete Votecatcher demo flow, showcasing the MVP features.

## Prerequisites

- Backend running on http://localhost:8000
- Frontend running on http://localhost:5173
- Sample data loaded (voter list + petition)

## Demo Flow

### Step 1: Create a Campaign

1. Navigate to **http://localhost:5173/workspace/campaigns**
2. Click **"Create Campaign"**
3. Fill in:
   - Name: "Demo Campaign 2024"
   - Year: "2024"
   - Region: Select "District of Columbia"
4. Click **"Create"**

### Step 2: Upload Voter List

1. Navigate to **http://localhost:5173/workspace/upload/voters**
2. Click **"Upload Voter List"**
3. Select `samples/dc/fake_voter_records.csv`
4. Watch upload progress
5. Verify success message

### Step 3: Upload Petition

1. Navigate to **http://localhost:5173/workspace/upload/petition**
2. Click **"Upload Petition"**
3. Select `samples/dc/fake_signed_petitions.pdf`
4. Watch upload progress
5. Verify pre-crop creation

### Step 4: Start OCR Job

1. Navigate to **http://localhost:5173/workspace/jobs**
2. Select your campaign from dropdown
3. Select OCR Provider: OpenAI (or Gemini/Mistral)
4. Click **"Start Job"**
5. Watch real-time progress via SSE

### Step 5: View Results

1. Navigate to **http://localhost:5173/workspace/results**
2. Filter by confidence level (All/High/Medium/Low)
3. Click on a row to see OCR text and top 5 predictions
4. Verify confidence badges

### Step 6: Export Results

1. Click **"Export CSV"** button
2. Download results spreadsheet

## Demo Reset

To reset all demo data:

1. Navigate to **http://localhost:5173/workspace/demo** (if demo mode enabled)
2. Click **"Reset Demo"**
3. Confirm reset

## Notes

- Sample data is located in `samples/dc/`
- Demo mode must `DEMO_MODE=true` in `.env`
- Demo reset needs `DEMO_RESET=true` in `.env`
