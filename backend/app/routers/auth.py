from datetime import datetime, timedelta, timezone
from typing import Annotated

from app.data import DbClient, get_db_client
from app.dependencies import oauth2_scheme
from app.schemas import AuthUser, Login, NewUser, SessionTokenResponse, SuccessResponse
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from supabase_auth import AuthResponse, Session, User, UserResponse

router: APIRouter = APIRouter(tags=["Auth"], prefix="/auth")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[DbClient, Depends(get_db_client)],
) -> AuthUser:

    try:
        response: UserResponse | None = await db.get_auth_user(token)
        if not response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user: User = response.user
        return AuthUser(id=user.id, email=user.email)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials\n{str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
):
    if not current_user:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/register")
async def signup_user(
    new_user: NewUser, db: Annotated[DbClient, Depends(get_db_client)]
) -> AuthUser:
    try:
        response: AuthResponse = await db.sign_up(
            email=new_user.email, password=new_user.password
        )
        user: User | None = response.user
        session: Session | None = response.session
        if response.user:
            return AuthUser(id=user.id, email=user.email)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User could not be created",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Signup failed: {str(e)}"
        )


@router.post("/login")
async def login(
    login: Login, db: Annotated[DbClient, Depends(get_db_client)]
) -> AuthUser:
    try:
        response: AuthResponse = await db.sign_in(
            email=login.email, password=login.password
        )
        user: User | None = response.user
        session: Session | None = response.session
        if user:
            return AuthUser(id=user.id, email=user.email)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Login unsuccessful"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Login failed: {str(e)}"
        )


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[DbClient, Depends(get_db_client)],
) -> SessionTokenResponse:
    response: AuthResponse = await db.sign_in(
        email=form_data.username, password=form_data.password
    )
    user: User | None = response.user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    session: Session | None = response.session

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to create authneticated session",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return SessionTokenResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_at=session.expires_at,
        expires_in=session.expires_in,
        token_type=session.token_type,
    )


@router.post("/api/refresh-token")
async def refresh_access_token(
    request: Request,
    response: Response,
    db: Annotated[DbClient, Depends(get_db_client)],
) -> SessionTokenResponse:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found in cookies",
        )

    try:
        res: AuthResponse = await db.create_new_auth_session(refresh_token)
        if res.session:
            session: Session = res.session
            new_access_token = session.access_token
            new_refresh_token = session.refresh_token

            # Update the HttpOnly cookie with the new refresh token
            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                samesite="strict",
                secure=False,  # Set to True in production
            )

            return SessionTokenResponse(
                access_token=new_access_token,
                refresh_token=session.refresh_token,
                token_type=session.token_type,
                expires_at=session.expires_at,
                expires_in=session.expires_in,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token",
            )
    except Exception as e:
        # If the refresh token itself is invalid or expired, force a full re-login
        response.delete_cookie("refresh_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to refresh session: {str(e)}",
        )


@router.post("/sign-out")
async def logout(db: Annotated[DbClient, Depends(get_db_client)]) -> SuccessResponse:
    db.sign_out()
    return SuccessResponse(message="Successfully logged out")
