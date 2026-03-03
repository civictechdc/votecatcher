This is a partially implemented web app that sends hand-written text to be OCR's by an LLM and compares it against a list of voters in a spreadsheet. It's in a mess due to several re-writes.

It's split into a python backend and a current rewrite as a svelte-front end (this will replace the existing front end)

Can you use your skills, tools, web or any other resources to study, plan and create a detailed implementation document for the following:

The current problem:

I need you to study both the backend backend/app/routers/ocr_route.py
and frontend:frontend-svelt/src/routes/workspace/[id]/+page.svelte

Fix the relevant back and front end parts to successfully display a results table with the correct ordered columns and associated row. It should be displayed as a paginated table on the front end.

We should add a way to simulate results that accurately reflects the state of the backend using openapi generated from the fast api.

For now try to do minimal adjustments without large or totally rewriting things if possible, while maintaining your skills on good coding practises. Write tests against working components, either unit or approval to maintain stability. You may adjust the database schema if neccessary.
