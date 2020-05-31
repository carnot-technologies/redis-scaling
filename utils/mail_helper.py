from django.conf import settings
from threading import Thread
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


def send_email_raw(sub, message, recipients=settings.RECIPIENTS):
    msg = MIMEMultipart()
    message = str(message)
    msg['From'] = settings.SERVER_EMAIL
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = str(sub)
    msg.attach(MIMEText(message, 'plain'))

    smtpObj = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
    smtpObj.starttls()
    smtpObj.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    smtpObj.sendmail(msg['From'], recipients, msg.as_string())
    smtpObj.close()


def send_email(subject, message, prefix=settings.EMAIL_PREFIX):
    if settings.ENABLE_EMAILS:
        modsub = prefix + " " + subject
        t = Thread(target=send_email_raw, args=(modsub, message,))
        t.start()


def mail_admins(subject, body):
    if settings.ENABLE_EMAILS:
        from django.core.mail import mail_admins as django_mail_admins
        modsub = settings.EMAIL_PREFIX + " - " + subject
        t = Thread(target=django_mail_admins, args=(modsub, body,))
        t.start()
