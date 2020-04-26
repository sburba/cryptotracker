import os
from distutils.util import strtobool

DATABASE_URL = os.environ["DATABASE_URL"]
SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
USE_REAL_MAILER = strtobool(os.environ["USE_REAL_MAILER"])
NOTIFY_EMAILS = os.environ["NOTIFY_EMAILS"].split(",")
