from mail_config import mail

def sendMail(subject, body, sender, recipients, html):
    mail.send_message(
        subject=subject,
        body=body,
        sender=sender,
        recipients=recipients,
        html=html
    )
