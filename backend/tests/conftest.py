import os

os.environ["DATABASE_URL"] = "sqlite:///file:memdb?mode=memory&cache=shared&uri=true"
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_SERVICE_KEY"] = ""
os.environ["SUPABASE_DB_PASSWORD"] = ""
