"""Tests for player loading functionality."""
import pytest
from uuid import UUID

from palworld_save_pal.dto.summary import PlayerSummary
from palworld_save_pal.game.save_file import SaveFile


class TestPlayerLoading:
    """Test suite for player loading from save files."""

    def test_player_file_refs_loaded(self, player_file_refs):
        """Test that player file references are correctly loaded."""
        assert len(player_file_refs) > 0, "No player file references loaded"
        
        # Verify structure: Dict[UUID, Dict[str, bytes]]
        for player_uuid, files in player_file_refs.items():
            assert isinstance(player_uuid, UUID), f"Player UUID should be UUID type, got {type(player_uuid)}"
            assert isinstance(files, dict), "Player files should be a dictionary"
            assert "sav" in files, "Player files should contain 'sav' key"
            assert isinstance(files["sav"], bytes), "Player save data should be bytes"

    def test_save_file_loads(self, loaded_save_file):
        """Test that the save file loads successfully."""
        assert loaded_save_file is not None, "Save file should be loaded"
        assert loaded_save_file._gvas_file is not None, "GVAS file should be loaded"
        assert loaded_save_file.world_name is not None, "World name should be set"

    def test_player_summaries_extracted(self, loaded_save_file):
        """Test that player summaries are extracted from the save file."""
        summaries = loaded_save_file.get_player_summaries()
        
        assert len(summaries) > 0, "No player summaries extracted"
        assert len(summaries) == 3, f"Expected 3 players, got {len(summaries)}"
        
        # Verify all summaries are PlayerSummary instances
        for player_id, summary in summaries.items():
            assert isinstance(player_id, UUID), "Player ID should be UUID"
            assert isinstance(summary, PlayerSummary), "Summary should be PlayerSummary instance"
            assert summary.uid == player_id, "Summary UID should match key"

    def test_all_expected_players_loaded(
        self, loaded_save_file, expected_players
    ):
        """Test that all expected players are loaded with correct names."""
        summaries = loaded_save_file.get_player_summaries()
        
        # Get player names from summaries
        loaded_names = {summary.nickname: summary for summary in summaries.values()}
        
        # Verify all expected players are present
        for expected_name in expected_players.keys():
            assert expected_name in loaded_names, (
                f"Expected player '{expected_name}' not found. "
                f"Loaded players: {list(loaded_names.keys())}"
            )

    def test_player_levels_correct(
        self, loaded_save_file, expected_players
    ):
        """Test that player levels are correctly extracted as integers."""
        summaries = loaded_save_file.get_player_summaries()
        
        # Create a mapping of nickname to summary
        name_to_summary = {summary.nickname: summary for summary in summaries.values()}
        
        for expected_name, expected_level in expected_players.items():
            assert expected_name in name_to_summary, (
                f"Player '{expected_name}' not found in summaries"
            )
            
            summary = name_to_summary[expected_name]
            
            # Verify level is an integer, not string
            assert summary.level is not None, (
                f"Player '{expected_name}' has no level"
            )
            assert isinstance(summary.level, int), (
                f"Player '{expected_name}' level should be int, got {type(summary.level)}: {summary.level}"
            )
            assert summary.level == expected_level, (
                f"Player '{expected_name}' level mismatch: expected {expected_level}, got {summary.level}"
            )

    def test_player_uuid_matching(self, loaded_save_file, player_file_refs):
        """Test that player UUIDs from CharacterSaveParameterMap match file references."""
        summaries = loaded_save_file.get_player_summaries()
        
        # All summaries should have corresponding file references
        for player_id, summary in summaries.items():
            assert player_id in player_file_refs, (
                f"Player {summary.nickname} (UID: {player_id}) not found in file references. "
                f"Available file ref UUIDs: {list(player_file_refs.keys())}"
            )
            
            # Verify the file reference has the required structure
            file_ref = player_file_refs[player_id]
            assert "sav" in file_ref, f"File reference for {summary.nickname} missing 'sav' key"
            assert isinstance(file_ref["sav"], bytes), (
                f"File reference 'sav' for {summary.nickname} should be bytes"
            )

    def test_player_summaries_have_required_fields(self, loaded_save_file):
        """Test that player summaries have all required fields."""
        summaries = loaded_save_file.get_player_summaries()
        
        for player_id, summary in summaries.items():
            assert summary.uid is not None, "Summary should have UID"
            assert summary.uid == player_id, "Summary UID should match key"
            assert summary.nickname is not None and summary.nickname != "", (
                f"Summary for {player_id} should have a nickname"
            )
            assert summary.level is not None, (
                f"Summary for {summary.nickname} should have a level"
            )
            assert isinstance(summary.level, int), (
                f"Level should be int, got {type(summary.level)}"
            )
            assert summary.level > 0, (
                f"Level should be positive, got {summary.level}"
            )

    def test_no_players_filtered_out(self, loaded_save_file):
        """Test that no players are incorrectly filtered out."""
        # Get both raw summaries and filtered summaries
        raw_summaries = loaded_save_file._player_summaries
        filtered_summaries = loaded_save_file.get_player_summaries()
        
        # All raw summaries should be in filtered summaries
        assert len(filtered_summaries) == len(raw_summaries), (
            f"Players were filtered out: {len(raw_summaries)} raw summaries, "
            f"{len(filtered_summaries)} filtered summaries. "
            f"Raw UUIDs: {[str(uid) for uid in raw_summaries.keys()]}, "
            f"Filtered UUIDs: {[str(uid) for uid in filtered_summaries.keys()]}"
        )

    def test_player_file_refs_count_matches(self, player_file_refs, loaded_save_file):
        """Test that the number of file refs matches the number of players."""
        summaries = loaded_save_file.get_player_summaries()
        
        # We should have at least as many file refs as players
        # (some players might not have DPS files)
        assert len(player_file_refs) >= len(summaries), (
            f"File refs ({len(player_file_refs)}) should be >= players ({len(summaries)})"
        )
        
        # All players should have file refs
        for player_id in summaries.keys():
            assert player_id in player_file_refs, (
                f"Player {player_id} missing file reference"
            )

    def test_uuid_normalization_works(self, loaded_save_file):
        """Test that UUID normalization works for matching."""
        summaries = loaded_save_file.get_player_summaries()
        
        # All summaries should have valid UUIDs
        for player_id, summary in summaries.items():
            assert isinstance(player_id, UUID), "Player ID should be UUID instance"
            assert str(player_id) != "", "Player ID should not be empty string"
            
            # UUID should be parseable
            from palworld_save_pal.utils.uuid import parse_uuid_from_string
            normalized = parse_uuid_from_string(str(player_id))
            assert normalized == player_id, "UUID normalization should preserve UUID"
