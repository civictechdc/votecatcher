# Votecatcher Customer Requirements

## Background

Votecatcher aims to help campaigns rapidly get snapshots of signed petition ballots against voting

## Problem

- Campaigns need to verify that the names and addresses on signed petitions match the names and addresses on their voter list.
- Current methods is manual visual verification, of paper petitions against an open spreadsheet with a list of voters which is slow, manual, tedious and very error prone.

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

### High Level Business Flow

#### Golden Path

1 - User sets up an instance
2 - User onboards and/or authenticates to a campaign
3 - User uploads a voter list or selects an existing list associated with the campaign
4 - User uploads scanned petition(s)
5 - User runs the asynchronous matching process
6 - User is informed of progress/phase - User view
7 - User recieves a well structured table of matching results
8 - User recieves dashboard displaying an array of relevant metrics

### Features

#### Campaign Management

- Campaigns tied to a season/year and region
- Users can be associated with multiple campaigns
- Campaign administration
  - User managment
- Branding customisation

#### OCR Model selection

- Provide API Keys
- Integrate provider SSO
- Enumerated list (can it be dynamically updated from a remote list)
- Optional: Local/self hosted model options
- Select vendor/models at runtime
- Campaign management
- User management
- Storage management and configuration
- Hosting configuration
- Data management
- Security and Access controls
- Structured branding configuration
- Model/vendor selection persisted for text extraction jobs/results

#### Asset storage

- Storing voter lists and associating them with region and date-time
- Shared voter list for multiple campaigns in the same region/year
- Petition scans
  - Crops?
- predictive, indexable naming
- Open questions about efficient storage/storage formats
- Asset export
- Duplication resolution

### Deployment and Release

- It's an open source product
- Allow for self-hosting deployment
  - Containers?
  - Bootstrap script to set up most of the core?
- One-click deployment to a cloud vendor
  - Digital ocean example: https://www.digitalocean.com/community/tutorials/one-click-deploy-button
- What can be automated and what requires manual or pre-set up
- Secure deployment

### Storage set-up

- Auto create local database
- Auto connect to host provider given required credentials e.g. supabase

## Key Milesone

### Deployable Minimum Viable Product

### Must-have Scope

- A working build that allows a complete end-to-end experince of creating a campaign, uploading files and running matches
  - Baseline acceptable performance
- Baseline UX/Styling
  - Along the lines of the current motif
  - Arrange in a modular way for future refinement
  - Baseline accessibility
- Basic campaign creation and configuration
  - Create campaign onboarding
    - Name, Description, Target election year
    - Editing the above fields
- Foundational database schema
  - Campaigns, Assets, Text extraction (jobs and results), Fuzzy matching (results)
  - User (lower priority)
  - Region (lower priority)
- Working with local databases like PostGres/SQLite or on a Supabase
- Contanerised deployment
- A first-pass impelemenation of simple/'one click' deployment (this can be iterated and optimised on)
  - Auto run database creation and schema set-up
  - Start backend and front end
- Foundatonal secure web practises
  - Credential management of keys
  - Frontend/backend data hygeine
  - Data leakage prevention
  - Hooks/support for HTTPS and encrypted data in the future

### Stretch goals

- Basic user auth and managment
- Regional configuration
  - Campaign creation selects a region which provides preset configurations on expected registered voter table fields and expected petiton fields

### Hosted Simulated Demo

- We want to have a variant of Votecatcher that is hosted on a public URL
- Users who visit this version will be able to interact with the core flow
- Simulate uploading files
- Simulate the UX of matching and results/metrics presentation
- No real external calls, all data and events are pre-baked or locally sourced
- Simulation can be reset
