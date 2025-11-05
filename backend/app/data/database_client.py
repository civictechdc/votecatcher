import os

from dotenv import load_dotenv
from postgrest import AsyncRequestBuilder
from supabase_auth import (
    AuthResponse,
    Session,
    SignInWithEmailAndPasswordCredentials,
    SignUpWithEmailAndPasswordCredentials,
    UserResponse,
)

from supabase import AsyncClient, acreate_client

load_dotenv()


async def _get_supabase_client() -> AsyncClient:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    assert url and key
    "SUPABASE_URL and SUPABASE_KEY required"
    supabase: AsyncClient = await acreate_client(supabase_url=url, supabase_key=key)
    return supabase


class DbClient:
    def __init__(self, supabase_client: AsyncClient):
        self.client: AsyncClient = supabase_client

    async def sign_up(self, email: str, password: str) -> AuthResponse:
        response: AuthResponse = await self.client.auth.sign_up(
            SignUpWithEmailAndPasswordCredentials(email=email, password=password)
        )
        return response

    async def sign_in(self, email: str, password: str) -> AuthResponse:
        response: AuthResponse = await self.client.auth.sign_in_with_password(
            SignInWithEmailAndPasswordCredentials(email=email, password=password)
        )
        return response

    async def get_auth_user(self, jwt: str) -> UserResponse | None:
        response: UserResponse | None = await self.client.auth.get_user(jwt=jwt)
        return response

    async def get_auth_session(self) -> Session | None:
        response: Session | None = await self.client.auth.get_session()
        return response

    async def create_new_auth_session(self, refresh_token: str) -> AuthResponse:
        response: AuthResponse = await self.client.auth.refresh_session(
            refresh_token=refresh_token
        )
        return response

    async def set_auth_session(
        self, access_token: str, refresh_token: str
    ) -> AuthResponse:
        response: AuthResponse = await self.client.auth.set_session(
            access_token=access_token, refresh_token=refresh_token
        )

        return response

    async def sign_out(self):
        await self.client.auth.sign_out()

    def table(self, table_name: str) -> AsyncRequestBuilder:
        return self.client.table(table_name)


async def get_db_client() -> DbClient:
    db_client = await _get_supabase_client()
    return DbClient(supabase_client=db_client)
