import polars as pl
from datetime import datetime
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def transform_clinic_data(source_path: str, destination_path: str, client_id: str = "00"):
    """
    Transforms raw clinic data from html to csv for sql bulk insert.

    :param source_path: Source of html file to be transformed
    :type source_path: str
    :param destination_path: Destination of csv file after transformation
    :type destination_path: str
    :param client_id: client_id
    :type client_id: str

    :raises Exception: If clinic data cannot be transformed or saved.
    """
    try:
        with open(source_path, "r", encoding="utf-8") as html_file:
            soup = BeautifulSoup(html_file, "lxml")

        table = soup.find("table", id="gvClinicList")

        headers = [th.get_text(strip=True) for th in table.find("tr", class_="DataGrid-Header").find_all("th")]

        rows = []

        for tr in table.find_all("tr", class_=["DataGrid-Item", "DataGrid-AlternatingItem"]):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            rows.append(cells)

        df = pl.DataFrame(rows, schema=headers, orient="row")
        df = df.with_columns(pl.lit(client_id).alias("ClientID"))
        df = df.with_columns(pl.lit(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]).alias("UpdatedAt"))
        df.write_csv(destination_path)
        logger.info("Clinic transformation completed successfully (%d rows written)", df.height)
    except Exception as e:
        logger.error("Clinic transformation failed: %s", e)
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    logger = logging.getLogger("Clinic data transformation example")
    source_path = r"C:\Users\Sinku\Documents\UC_AFC\UC_Experity_Automation\downloads\16\2026-01-02\ClinicData.html"
    destination_path = r"C:\Users\Sinku\Documents\UC_AFC\UC_Experity_Automation\downloads\16\2026-01-02\ClinicData.csv"
    transform_clinic_data(source_path, destination_path)
