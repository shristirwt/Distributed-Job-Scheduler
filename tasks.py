import logging

logger = logging.getLogger("tasks")


def generate_report():
    logger.info("Generating report...")
    logger.info("Report generated successfully!")


def send_email():
    logger.info("Sending email...")
    logger.info("Email sent successfully!")


def backup_database():
    logger.info("Starting database backup...")
    logger.info("Database backup completed successfully!")
    

JOB_FUNCTIONS = {
    "generate_report": {
        "function": generate_report,
        "description": "Generates a report"
    },
    "send_email": {
        "function": send_email,
        "description": "Sends an email"
    },
    "backup_database": {
        "function": backup_database,
        "description": "Creates a database backup"
    }
}