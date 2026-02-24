from datetime import datetime


def download_dir_date():
    return datetime.now().strftime("%d-%m-%Y")
