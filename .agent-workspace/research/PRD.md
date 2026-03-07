# Votecatcher Customer Requirements

## Background

Votecatcher aims to help campaigns rapidly get snapshots of signed petition ballots against voting

## Problem

- Campaigns need to verify that the names and addresses on signed petitions match the names and addresses on their voter list.
- Current methods is manual visual verification, which is slow, manual, tedious and very error prone

## Proposed Solution

- Use a combination of LLM/AI OCR and locally run fuzzy match to perform a predicted series of matches with a gague of confidence (e.g. Green/Amber/Red against each match entry)
- LLM/AI OCR models to parse scanned petitions and extract the hand-written names and addresses and return as structured data.
- The extracted texts are then passed into a fuzzy match alghorithm that will attempt to score and match each extracted names/address (and other relevant fields) item against the list of registered voters
- Batch process OCR on scanned petitions using available batch APIs from LLM vendors. Some examples include but not limited to:
  - OpenAI: https://developers.openai.com/api/docs/guides/batch/
  - Gemini Batch API:https://ai.google.dev/gemini-api/docs/batch-api?batch=file
  - Mistral Batch API:https://mistral.ai/news/batch-api
- Match results should be presented in an intuitive way to provide high level metrics on confidence on matches e.g. 80% 'high' confidence matches, 13% 'medium' confidence matches, 7% 'low' confidence matches
- Each match result entry is displayed in a strctured table format that enables the following:
  - The source and prediction column fields should be next to each other
  - The Table columns are adaptable based upon the petition field requirements
  - Each entry has a field showing the cropped scan of the petiton entry the text was extracted from e.g. a cropped image of the hand-written name and address
  - Each entry from the predicted column should have the ability to click to see the top 3 (or top 5) predictions as comparison
  - Table should be paginated and sortable/filterable
  - Matched sessions and results should be persisted to database with options to use locally created postgres or cloud services like supabase
  - Parallelise batch text extraction calls to reduce wait time from external LLM API while keeping within usage/cost limits
  - Saving any ids or records of ongoing asynchronous text extraction jobs:
    - date-time started
    - Current status
    - Any error messages
    - Date-time concluded (completed, error, timeout etc)
    - Associated campaign/region
    - OCR service used and model used
  - Dashboard showing signature progression
    - Number of high confidence matches
    - Regional breakdown (if applicable)
    - Comparing to target total e.g. percentages, raw totals

### Campaign Management

- Campaigns tied to a season/year and region
- Users can be associated with multiple campaigns
- Campaign administration
  - User managment
- Branding customisation

### Configuration

#### OCR Model selection

- Provide API Keys
- Integrate provider SSO
- Enumerated list (can it be dynamically updated from a remote list)
- Optional: Local/self hosted model options
  -Campaign management
- User management
- Storage management and configuration
- Hosting configuration
- Data management
- Security and Access controls
- Structured branding configuration

#### Asset storage

- Storing voter lists and associating them with region and date-time
- Shared voter list for multiple campaigns in the same region/year
- Petition scans
  - Crops?
- predictive, indexable naming
- Open questions about efficient storage/storage formats
- Asset export
- Duplication resolution
