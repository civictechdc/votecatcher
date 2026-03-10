import os

from dotenv import load_dotenv
from supabase import AsyncClient, Client, acreate_client, create_client

load_dotenv()


async def create_async_supabase_client() -> AsyncClient:
	try:
		url = os.getenv("SUPABASE_URL")
		key = os.getenv("SUPABASE_KEY")
		assert url and key, "SUPABASE_URL and SUPABASE_KEY required"
		supabase: AsyncClient = await acreate_client(supabase_url=url, supabase_key=key)
		return supabase
	except Exception:
		raise ValueError(
			"Unable to load supabase client. "
			"Please check that SUPABASE_URL and SUPABASE_KEY are set correctly."
		) from None


def create_supabase_client() -> Client:
	try:
		url = os.getenv("SUPABASE_URL")
		key = os.getenv("SUPABASE_KEY")
		assert url and key, "SUPABASE_URL and SUPABASE_KEY required"
		supabase: Client = create_client(supabase_url=url, supabase_key=key)
		return supabase
	except Exception:
		raise ValueError(
			"Unable to load supabase client. "
			"Please check that SUPABASE_URL and SUPABASE_KEY are set correctly."
		) from None
