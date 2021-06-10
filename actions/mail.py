from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import logging
import smtplib
from smtplib import SMTPException

class Mail:
    def __init__(self, **kwargs):
        server = kwargs.get('server', 'localhost')
        self.server = smtplib.SMTP(server)

    def compose_mail(self, message_text, from_addr, to_addr, **kwargs ) -> MIMEMultipart:
        subject = kwargs.get('subject')
        cc_addr = kwargs.get('cc_addr')
        bcc_addr = kwargs.get('bcc_addr')
        attached_file = kwargs.get('attached_file')
        """Composes MIMEMultipart and attaches attached_file"""
        self.msg = MIMEMultipart()
        text = MIMEText(message_text, 'plain', 'utf8')
        self.msg.attach(text)

        if attached_file:
            with open(attached_file, 'r') as f:
                attachment = MIMEText(f.read(), "plain", "utf-8")
            attachment.add_header('Content-Disposition', 'attachment', filename=attached_file)
            self.msg.attach(attachment)

        self.msg['Subject'] = subject
        self.msg['From'] = from_addr
        self.msg['To'] = COMMASPACE.join(to_addr)
        if cc_addr:
            self.msg['CC'] = COMMASPACE.join(cc_addr)
        if bcc_addr:
            self.msg['Bcc'] = COMMASPACE.join(bcc_addr)
        self.msg['Date'] = formatdate(localtime=True)

    def send_mail(self, from_addr, to_addr):
        """Sends mail using values given"""
        try:
            self.server.sendmail(from_addr, to_addr, self.msg.as_string())
            logging.info("Mail was successfully sent!")
        except SMTPException:
            logging.error("Error: mail was not sent!")
        finally:
            self.disconnect()

    def connect(self):
        self.server.connect()
        #self.server.login(self.conf.get('mail', 'smtp_user'), self.conf.get('mail', 'smtp_pass'))

    def disconnect(self):
        self.server.quit()

 
