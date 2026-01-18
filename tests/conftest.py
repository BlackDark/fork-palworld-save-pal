"""Pytest configuration and fixtures for player loading tests."""
from pathlib import Path
from typing import Dict
from uuid import UUID

import pytest

from palworld_save_pal.game.save_file import SaveFile
from palworld_save_pal.utils.file_manager import FileManager


@pytest.fixture
def save_file_dir() -> Path:
    """Return the path to the test save file directory."""
    return Path(__file__).parent.parent / "save" / "0AF5EB784DD4DD7F83A17BBF74FC5DE3"


@pytest.fixture
def level_sav_path(save_file_dir: Path) -> Path:
    """Return the path to Level.sav."""
    return save_file_dir / "Level.sav"


@pytest.fixture
def level_meta_sav_path(save_file_dir: Path) -> Path:
    """Return the path to LevelMeta.sav."""
    return save_file_dir / "LevelMeta.sav"


@pytest.fixture
def players_dir(save_file_dir: Path) -> Path:
    """Return the path to the Players directory."""
    return save_file_dir / "Players"


@pytest.fixture
def level_sav_bytes(level_sav_path: Path) -> bytes:
    """Load Level.sav as bytes."""
    with open(level_sav_path, "rb") as f:
        return f.read()


@pytest.fixture
def level_meta_sav_bytes(level_meta_sav_path: Path) -> bytes:
    """Load LevelMeta.sav as bytes."""
    with open(level_meta_sav_path, "rb") as f:
        return f.read()


@pytest.fixture
def player_file_refs(players_dir: Path) -> Dict[UUID, Dict[str, bytes]]:
    """Load player save files as bytes."""
    return FileManager.get_player_saves(str(players_dir))


@pytest.fixture
async def loaded_save_file(
    level_sav_bytes: bytes,
    level_meta_sav_bytes: bytes,
    player_file_refs: Dict[UUID, Dict[str, bytes]],
) -> SaveFile:
    """Load and return a SaveFile instance with the test save data."""
    save_file = SaveFile(level_sav_path="0AF5EB784DD4DD7F83A17BBF74FC5DE3")
    
    async def dummy_callback(msg: str):
        """Dummy callback for progress messages."""
        pass
    
    await save_file.load_sav_files(
        level_sav=level_sav_bytes,
        player_file_refs=player_file_refs,
        level_meta=level_meta_sav_bytes,
        ws_callback=dummy_callback,
    )
    
    return save_file


@pytest.fixture
def expected_players() -> Dict[str, int]:
    """Return expected player names and levels."""
    return {
        "Knecht": 47,
        "Nugget": 43,
        "BlackDark": 42,
    }


# Note: pytest-asyncio handles event loop management automatically
# when asyncio_mode=auto is set in pytest.ini
