import os
import logging
from datetime import datetime

from bs4 import BeautifulSoup
import polars as pl

from parser import data_load_parser

parser = data_load_parser()
args = parser.parse_args()

logger = logging.getLogger("Experity_Automation")

CLIENT_ID = args.client_id
DATE_STAMP = str(datetime.now().strftime("%Y-%m-%d"))

if args.terminal_output:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
else:
    logs_dir = os.path.join("logs", DATE_STAMP)
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, f"data_load_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.log")
    logging.basicConfig(filename=log_file, filemode="a", level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")

DOWNLOAD_DIR = os.path.join("downloads", DATE_STAMP, CLIENT_ID)


def html_table_to_csv(
    html_path: str,
    csv_out: str,
    client_id: str,
    table_id: str = "gvClinicList",
):
    """
    Parse HTML table -> Polars DataFrame -> CSV

    :param html_path: path to HTML file
    :param table_id: table id attribute (e.g. "gvClinicList")
    :param csv_out: output csv file path
    :return: Polars DataFrame
    """

    # ---------- HTML PARSE ----------
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    table = soup.find("table", {"id": table_id})
    if table is None:
        raise ValueError(f"Table with id '{table_id}' not found")

    rows = table.find_all("tr")

    # header
    headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]

    # data
    records = []
    for r in rows[1:]:
        cols = [td.get_text(strip=True) for td in r.find_all("td")]
        if cols:
            records.append(cols)

    # ---------- POLARS ----------
    df = pl.DataFrame(records, schema=headers)
    df = df.with_columns(pl.lit(client_id).alias("ClientID"))

    # ---------- CSV ----------
    df.write_csv(csv_out)

    return df


clinic_data_path = os.path.join(DOWNLOAD_DIR, "ClinicData.html")
try:
    logger.info("Starting clinic data transformation for Client ID: %s", CLIENT_ID)
    csv_path = clinic_data_path[:-4] + "csv"
    html_table_to_csv(clinic_data_path, csv_path, CLIENT_ID)
    logger.info("Completed clinic data transformation for Client ID: %s", CLIENT_ID)
    logger.info("Transformed csv path: %s", csv_path)
except FileNotFoundError:
    logger.error("File don't exist at: %s", clinic_data_path)
except Exception as e:
    logger.error("Unknown error occured while transformations for Client ID: %s", CLIENT_ID)
    logger.error("Error: %s", e)
