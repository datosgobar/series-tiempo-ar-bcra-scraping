from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import logging
import smtplib
import yaml
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_EMAIL_PATH = os.path.join(ROOT_DIR, "email.yaml")

class Email:

    def __init__(self):
        super().__init__()

    def send_email(self, mailer_config, subject, message, recipients):
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = mailer_config["user"]
        msg["To"] = ",".join(recipients)
        msg["Date"] = formatdate(localtime=True)

        msg.attach(MIMEText(message))

        try:
            if mailer_config["ssl"]:
                s = smtplib.SMTP_SSL(
                    mailer_config["smtp_server"], mailer_config["port"])
            else:
                s = smtplib.SMTP(
                    mailer_config["smtp_server"], mailer_config["port"])
                s.ehlo()
                s.starttls()
                s.ehlo()
            s.login(mailer_config["user"], mailer_config["password"])
            s.sendmail(mailer_config["user"], recipients, msg.as_string())
            s.close()
            logging.info(f"Se envió exitosamente un reporte a {', '.join(recipients)}")
        except Exception as e:
            logging.info(f'Error al enviar mail: {repr(e)}')

    def send_validation_group_email(self, execution_start_time, execution_end_time, start_date, end_date, skip_intermediate_panel_data, identifier):
        config_mail = self.read_config_mail()
        mailer_config = self.get_mailer(config_mail)

        try:
            subject = self.generate_subject(identifier)
            message = self.generate_message(execution_start_time, execution_end_time, start_date, end_date, skip_intermediate_panel_data)

            recipients = config_mail.get('destinatarios', [])
            if recipients:
                logging.info(f"Enviando reporte...")
                self.send_email(mailer_config, subject, message, recipients)
            else:
                logging.warning('No hay destinatarios')
        except Exception:
            raise

    def read_config_mail(self):
        cfg = {}
        try:
            with open(CONFIG_EMAIL_PATH, 'r') as ymlfile:
                cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        except (IOError, yaml.parser.ParserError):
            logging.warning(
                "No se pudo cargar el archivo de configuración 'config_email.yaml'.")
            logging.warning("Salteando envío de mails...")
            cfg = None

        return cfg

    def get_mailer(self, config_mail):
        try:
            mailer_config = config_mail['mailer']
            return mailer_config
        except Exception:
            logging.info(f'Error en la configuración para el envío de mails')

    def generate_subject(self, identifier):
        subject = self._get_mail_subject(identifier)
        return subject

    def generate_message(self, execution_start_time, execution_end_time, start_date, end_date, skip_intermediate_panel_data):
        message = (
            f"Corrida del scraper con los siguientes parámetros: \n"
            f"Fecha de inicio: {start_date}\n"
            f"Fecha de fin: {end_date}\n"
            f"Saltear panel intermedio: {self.get_skip_intermediate_panel_data(skip_intermediate_panel_data)}\n"
            "Tiempo transcurrido de corrida: \n"
            f"Horario de inicio de corrida: {execution_start_time} \n"
            f"Horario de fin de corrida: {execution_end_time}"
        )

        return message

    def get_skip_intermediate_panel_data(self, skip_intermediate_panel_data):
        if skip_intermediate_panel_data:
            skip_intermediate_panel_data = 'Si'
        else:
            skip_intermediate_panel_data = 'No'
        return skip_intermediate_panel_data

    def _get_mail_subject(self, identifier):
        subject = f"Resultados del scraper {identifier}"
        return subject
