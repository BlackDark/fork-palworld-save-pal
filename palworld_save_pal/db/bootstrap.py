import os
import platform
import sys
from sqlmodel import SQLModel, create_engine

from palworld_save_pal.editor.preset_profile import PalPreset, PresetProfile
from palworld_save_pal.db.models.settings_model import SettingsModel
from palworld_save_pal.db.models.ups_models import (
    UPSPalModel,
    UPSCollectionModel, 
    UPSTagModel,
    UPSStatsModel,
    UPSTransferLogModel
)
from palworld_save_pal.utils.logging_config import create_logger
from palworld_save_pal.db.migration import run_migrations

logger = create_logger(__name__)

# Allow database path to be configured via environment variable
# Default to "psp.db" in current directory
DB_PATH = os.getenv("PSP_DB_PATH", "psp.db")

# If we're on Mac and frozen, make sure we use the correct path
if getattr(sys, "frozen", False) and platform.system() == "Darwin":
    # The application is frozen
    if not os.getenv("PSP_DB_PATH"):
        # Only override if not explicitly set via environment variable
        DB_PATH = os.path.join(os.path.dirname(sys.executable), "psp.db")

# Ensure absolute path for SQLite URL
if not os.path.isabs(DB_PATH):
    DB_PATH = os.path.abspath(DB_PATH)

# Ensure the directory for the database file exists
db_dir = os.path.dirname(DB_PATH)
if db_dir:
    try:
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, mode=0o755, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")
        # Verify the directory is writable
        if not os.access(db_dir, os.W_OK):
            logger.warning(f"Database directory {db_dir} is not writable")
    except OSError as e:
        logger.error(f"Failed to create database directory {db_dir}: {e}")
        raise

logger.info(f"Database will be stored at: {DB_PATH}")

SQLITE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(SQLITE_URL, echo=False)


def create_db_and_tables():
    # Double-check directory exists and is writable before proceeding
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, mode=0o755, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")
        except OSError as e:
            logger.error(f"Failed to create database directory {db_dir}: {e}")
            raise
    
    # Verify write permissions
    if db_dir and not os.access(db_dir, os.W_OK):
        logger.error(f"Database directory {db_dir} is not writable. Check permissions.")
        raise PermissionError(f"Cannot write to database directory: {db_dir}")
    
    if os.path.exists(DB_PATH):
        logger.info(
            f"Existing database found at {DB_PATH}, checking for schema updates"
        )
        try:
            run_migrations(DB_PATH)
        except Exception as e:
            logger.warning(f"Migration check failed: {e}, continuing anyway")

    try:
        SQLModel.metadata.create_all(engine)
        logger.info(f"Database setup complete at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to create database at {DB_PATH}: {e}")
        logger.error(f"Database directory: {db_dir}, exists: {os.path.exists(db_dir) if db_dir else 'N/A'}, writable: {os.access(db_dir, os.W_OK) if db_dir else 'N/A'}")
        raise
