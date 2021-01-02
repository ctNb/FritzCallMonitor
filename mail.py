import smtplib


def send_mail(config, subject, content):
    port = config["mail"]["smtp-port"]
    password = config["mail"]["password"]
    smtp_server = config["mail"]["smtp-server"]

    sender_address = config["mail"]["sender-address"]
    receiver_addresses = config["mail"]["receiver-addresses"]

    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()
        server.starttls()
        server.login(sender_address, password)
        message = f"From: {sender_address}\n" + f"To: {';'.join(receiver_addresses)}\n" + f"Subject: {subject}\n\n" + f"{content}"
        server.sendmail(sender_address, receiver_addresses, message)
