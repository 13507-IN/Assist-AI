import asyncio
import base64
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.config import is_configured, settings


logger = logging.getLogger(__name__)
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


class GmailService:
    def configured(self) -> bool:
        return is_configured(settings.gmail_client_id) and is_configured(
            settings.gmail_client_secret
        )

    def _client_config(self) -> dict:
        return {
            "web": {
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": TOKEN_URI,
                "redirect_uris": [settings.gmail_redirect_uri],
            }
        }

    def authorization_url(self, state: str) -> tuple[str, Optional[str]]:
        if not self.configured():
            raise RuntimeError(
                "Missing GMAIL_CLIENT_ID and/or GMAIL_CLIENT_SECRET in backend/.env"
            )
        flow = Flow.from_client_config(
            self._client_config(),
            scopes=GMAIL_SCOPES,
            state=state,
        )
        flow.redirect_uri = settings.gmail_redirect_uri
        url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return url, flow.code_verifier

    async def exchange_code(
        self,
        code: str,
        state: str,
        db,
        user_id: str,
        code_verifier: Optional[str] = None,
    ) -> str:
        flow = Flow.from_client_config(
            self._client_config(),
            scopes=GMAIL_SCOPES,
            state=state,
            code_verifier=code_verifier,
            autogenerate_code_verifier=False,
        )
        flow.redirect_uri = settings.gmail_redirect_uri
        await asyncio.to_thread(flow.fetch_token, code=code)
        credentials = flow.credentials

        existing = await db.oauth_tokens.find_one({"user_id": user_id})
        refresh_token = credentials.refresh_token or (existing or {}).get("refresh_token")
        if not refresh_token:
            raise RuntimeError(
                "Google did not return a refresh token. Revoke the app grant and sign in again."
            )
        credentials.refresh_token = refresh_token
        email = await self._profile_email(credentials)
        await self._save_credentials(db, user_id, credentials, email)
        return email

    async def _profile_email(self, credentials: Credentials) -> str:
        service = await asyncio.to_thread(
            build,
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )
        profile = await asyncio.to_thread(service.users().getProfile(userId="me").execute)
        return profile.get("emailAddress", "")

    async def _save_credentials(
        self,
        db,
        user_id: str,
        credentials: Credentials,
        email: Optional[str] = None,
    ) -> None:
        update = {
            "user_id": user_id,
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri or TOKEN_URI,
            "scopes": list(credentials.scopes or GMAIL_SCOPES),
            "expiry": credentials.expiry,
            "updated_at": datetime.now(timezone.utc),
        }
        if email:
            update["email"] = email
        await db.oauth_tokens.update_one(
            {"user_id": user_id},
            {"$set": update, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
            upsert=True,
        )

    async def credentials(self, db, user_id: str) -> tuple[Credentials, dict]:
        token = await db.oauth_tokens.find_one({"user_id": user_id})
        if not token:
            raise RuntimeError("Gmail is not connected")
        credentials = Credentials(
            token=token.get("token"),
            refresh_token=token.get("refresh_token"),
            token_uri=token.get("token_uri", TOKEN_URI),
            client_id=settings.gmail_client_id,
            client_secret=settings.gmail_client_secret,
            scopes=token.get("scopes") or GMAIL_SCOPES,
        )
        expiry = token.get("expiry")
        if expiry:
            credentials.expiry = expiry.replace(tzinfo=None) if expiry.tzinfo else expiry
        if not credentials.valid:
            if not credentials.refresh_token:
                raise RuntimeError("Gmail token expired and has no refresh token")
            await asyncio.to_thread(credentials.refresh, Request())
            await self._save_credentials(db, user_id, credentials, token.get("email"))
        return credentials, token

    async def status(self, db=None, user_id: str = "local-user") -> dict:
        if not self.configured():
            return {
                "status": "error",
                "configured": False,
                "connected": False,
                "detail": "Missing GMAIL_CLIENT_ID and/or GMAIL_CLIENT_SECRET in backend/.env",
            }
        if db is None:
            return {
                "status": "disconnected",
                "configured": True,
                "connected": False,
                "detail": "MongoDB is unavailable, so the Gmail token cannot be loaded",
            }
        try:
            credentials, token = await self.credentials(db, user_id)
            email = token.get("email") or await self._profile_email(credentials)
            return {
                "status": "ok",
                "configured": True,
                "connected": True,
                "email": email,
                "detail": f"Connected as {email}",
            }
        except RuntimeError as exc:
            return {
                "status": "disconnected",
                "configured": True,
                "connected": False,
                "detail": str(exc),
            }
        except Exception as exc:
            return {
                "status": "error",
                "configured": True,
                "connected": False,
                "detail": str(exc),
            }

    async def send_email(
        self,
        db,
        user_id: str,
        to_email: str,
        subject: str,
        body: str,
    ) -> dict:
        try:
            credentials, token = await self.credentials(db, user_id)
            message = MIMEText(body)
            message["to"] = to_email
            message["subject"] = subject
            if token.get("email"):
                message["from"] = token["email"]
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service = await asyncio.to_thread(
                build,
                "gmail",
                "v1",
                credentials=credentials,
                cache_discovery=False,
            )
            result = await asyncio.to_thread(
                service.users().messages().send(
                    userId="me",
                    body={"raw": raw},
                ).execute
            )
            return {"success": True, "message_id": result.get("id")}
        except Exception as exc:
            logger.error("Gmail send failed: %s", exc)
            return {"success": False, "error": str(exc)}
