from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import smtplib
import ssl
from typing import Protocol


class PasswordResetMailer(Protocol):
    def send_password_reset(self, recipient: str, reset_url: str, expires_minutes: int) -> None: ...


class DisabledPasswordResetMailer:
    def send_password_reset(self, recipient: str, reset_url: str, expires_minutes: int) -> None:
        return None


@dataclass(frozen=True, slots=True)
class SmtpPasswordResetMailer:
    host: str
    port: int
    sender: str
    username: str | None = None
    password: str | None = None
    starttls: bool = True
    use_ssl: bool = False
    timeout_seconds: float = 10

    def send_password_reset(self, recipient: str, reset_url: str, expires_minutes: int) -> None:
        message = EmailMessage()
        message["Subject"] = "[M-Journey] 비밀번호 재설정 안내"
        message["From"] = self.sender
        message["To"] = recipient
        message.set_content(
            "M-Journey 비밀번호 재설정 요청이 접수되었습니다.\n\n"
            f"아래 링크는 {expires_minutes}분 동안 한 번만 사용할 수 있습니다.\n"
            f"{reset_url}\n\n"
            "본인이 요청하지 않았다면 이 메일을 무시해주세요."
        )

        smtp_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
        kwargs = {"host": self.host, "port": self.port, "timeout": self.timeout_seconds}
        if self.use_ssl:
            kwargs["context"] = ssl.create_default_context()
        with smtp_class(**kwargs) as client:
            if self.starttls and not self.use_ssl:
                client.starttls(context=ssl.create_default_context())
            if self.username and self.password:
                client.login(self.username, self.password)
            client.send_message(message)


def build_password_reset_mailer(
    *,
    host: str | None,
    port: int,
    sender: str | None,
    username: str | None,
    password: str | None,
    starttls: bool,
    use_ssl: bool,
) -> PasswordResetMailer:
    if not host:
        return DisabledPasswordResetMailer()
    if not sender:
        raise ValueError("SMTP를 사용할 때 M_JOURNEY_SMTP_FROM이 필요합니다.")
    if bool(username) != bool(password):
        raise ValueError("SMTP 사용자명과 비밀번호는 함께 설정해야 합니다.")
    if starttls and use_ssl:
        raise ValueError("SMTP STARTTLS와 SSL은 동시에 사용할 수 없습니다.")
    return SmtpPasswordResetMailer(
        host=host,
        port=port,
        sender=sender,
        username=username,
        password=password,
        starttls=starttls,
        use_ssl=use_ssl,
    )
