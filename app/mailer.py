from abc import ABC, abstractmethod
from logging import Logger

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class Mailer(ABC):
    @abstractmethod
    def send_mail(self, email: str, subject: str, contents: str) -> None:
        """
        Send an email to the specified recipient

        :param email: Destination email address
        :param subject: Email subject line
        :param contents: May be HTML if necessary
        :return:
        """
        ...


class LoggingMailer(Mailer):
    def __init__(self, logger: Logger):
        self._logger = logger

    def send_mail(self, email: str, subject: str, contents: str) -> None:
        self._logger.info(
            "Sending mail: %s",
            {"email": email, "subject": subject, "contents": contents},
        )


class SendGridMailer(Mailer):
    def __init__(self, sendgrid_api: SendGridAPIClient):
        self._sendgrid_api = sendgrid_api

    def send_mail(self, email: str, subject: str, contents: str) -> None:
        message = Mail(
            from_email="cryptotracker@samburba.com",
            to_emails=email,
            subject="Cryptotracker Alert",
            html_content=contents,
        )

        # TODO: Log request/response details, handle exceptions
        # TODO: This API sends network traffic synchronously
        # This will block the event loop. We need to wrap it so
        # it happens asynchronously
        self._sendgrid_api.send(message)
