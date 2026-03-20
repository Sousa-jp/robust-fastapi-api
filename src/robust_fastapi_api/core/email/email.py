from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from fastapi_mail import FastMail, MessageSchema, MessageType
from fastapi_mail.connection import ConnectionConfig
from fastapi_mail.errors import ConnectionErrors
from jinja2 import Environment, FileSystemLoader
from pydantic import EmailStr

from ...core.settings import settings


@dataclass
class EmailTemplate:
    template_name: str
    subject: str
    variables: dict[str, str]


class EmailClient:
    def __init__(self) -> None:
        config = ConnectionConfig(
            MAIL_USERNAME=settings.email.email_username,
            MAIL_PASSWORD=settings.email.email_password,
            MAIL_FROM=settings.email.email_from,
            MAIL_FROM_NAME=settings.email.from_name,
            MAIL_PORT=settings.email.email_port,
            MAIL_SERVER=settings.email.email_host,
            MAIL_STARTTLS=settings.email.use_tls,
            MAIL_SSL_TLS=settings.email.use_ssl,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
            SUPPRESS_SEND=settings.email.suppress_send,
        )
        self._fastmail = FastMail(config)
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self._jinja_env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)

    async def send_email(self, recipients: List[EmailStr], template: EmailTemplate) -> None:
        try:
            template_obj = self._jinja_env.get_template(f"{template.template_name}.html")
            body = template_obj.render(**template.variables)
            subject = self._jinja_env.from_string(template.subject).render(**template.variables)
            message = MessageSchema(
                subject=subject,
                recipients=recipients,
                body=body,
                subtype=MessageType.html,
            )
            await self._fastmail.send_message(message)
        except Exception as e:
            raise ConnectionErrors(f"Error sending email: {str(e)}") from e


def get_email_client() -> EmailClient:
    return EmailClient()
