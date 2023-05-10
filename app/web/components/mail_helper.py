from mail_config import mail

def send_activation_email(subject, body, sender, recipients, html):
    mail.send_message(
        subject=subject,
        body=body,
        sender=sender,
        recipients=recipients,
        html=html
    )
