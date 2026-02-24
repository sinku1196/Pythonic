import os
from datetime import datetime
from typing import Optional


def use_directory(
    client_id: str,
    base_path: Optional[str] = None,
    directory: str = "downloads",
    date: Optional[str] = None  # expected format: DD-MM-YYYY
) -> str:
    """
    Build a structured filesystem path for client-specific storage.

    Directory structure:
        <base_path or cwd>/<directory>/<date>/<client_id>

    Examples:
        ./downloads/13-02-2026/client123
        /data/storage/downloads/13-02-2026/client123

    Args:
        client_id (str):
            Unique identifier for the client/user.
        base_path (Optional[str]):
            Root directory to use instead of current working directory.
            If None, os.getcwd() is used.
        directory (str):
            Top-level directory name (e.g. "downloads", "screenshots").
        date (Optional[str]):
            Date folder name in format DD-MM-YYYY.
            If None, current date is auto-generated.

    Returns:
        str: Fully constructed directory path.
    """

    # Determine date folder
    if date:
        date_folder = date
    else:
        date_folder = datetime.now().strftime("%d-%m-%Y")

    # Determine base directory
    root = base_path if base_path else os.getcwd()

    return os.path.join(root, directory, date_folder, client_id)


def download_directory(
    client_id: str,
    base_path: Optional[str] = None,
    date: Optional[str] = None,
    create: bool = True
) -> str:
    """
    Get (and optionally create) a download directory for a client.

    Structure:
        <base_path or cwd>/downloads/<date>/<client_id>

    Args:
        client_id (str):
            Unique identifier for the client/user.
        base_path (Optional[str]):
            Root directory override.
        date (Optional[str]):
            Date folder in format DD-MM-YYYY.
        create (bool):
            If True, creates the directory tree if it does not exist.

    Returns:
        str: Absolute path to the download directory.
    """

    path = use_directory(
        client_id=client_id,
        base_path=base_path,
        directory="downloads",
        date=date
    )

    if create:
        os.makedirs(path, exist_ok=True)

    return path


def screenshot_directory(
    client_id: str,
    base_path: Optional[str] = None,
    date: Optional[str] = None,
    create: bool = True
) -> str:
    """
    Get (and optionally create) a screenshot directory for a client.

    Structure:
        <base_path or cwd>/screenshots/<date>/<client_id>

    Args:
        client_id (str):
            Unique identifier for the client/user.
        base_path (Optional[str]):
            Root directory override.
        date (Optional[str]):
            Date folder in format DD-MM-YYYY.
        create (bool):
            If True, creates the directory tree if it does not exist.

    Returns:
        str: Absolute path to the screenshot directory.
    """

    path = use_directory(
        client_id=client_id,
        base_path=base_path,
        directory="screenshots",
        date=date
    )

    if create:
        os.makedirs(path, exist_ok=True)

    return path
