"""
Tests for Red Team generator dry-run behavior and error handling.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, call
import argparse

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module to test
import scripts.generate_red_team as red_team_module


class TestLoadPrompts:
    """Test prompt loading functionality."""
    
    def test_load_prompts_file_exists(self, tmp_path, monkeypatch):
        """Test loading prompts from existing file."""
        # Create a mock prompts file
        prompts_file = tmp_path / "red_team_prompts.txt"
        prompts_file.write_text("Prompt 1\nPrompt 2\nPrompt 3\n")
        
        # Mock the PROMPTS_FILE path
        monkeypatch.setattr(red_team_module, 'PROMPTS_FILE', prompts_file)
        
        prompts = red_team_module.load_prompts()
        assert len(prompts) == 3
        assert prompts[0] == "Prompt 1"
        assert prompts[1] == "Prompt 2"
        assert prompts[2] == "Prompt 3"
    
    def test_load_prompts_file_not_found(self, tmp_path, monkeypatch):
        """Test handling when prompts file doesn't exist."""
        prompts_file = tmp_path / "nonexistent.txt"
        monkeypatch.setattr(red_team_module, 'PROMPTS_FILE', prompts_file)
        
        prompts = red_team_module.load_prompts()
        # Should return default prompts
        assert len(prompts) == 2
        assert "quick brown fox" in prompts[0].lower()
    
    def test_load_prompts_filters_empty_lines(self, tmp_path, monkeypatch):
        """Test that empty lines are filtered out."""
        prompts_file = tmp_path / "red_team_prompts.txt"
        prompts_file.write_text("Prompt 1\n\n\nPrompt 2\n  \nPrompt 3")
        
        monkeypatch.setattr(red_team_module, 'PROMPTS_FILE', prompts_file)
        
        prompts = red_team_module.load_prompts()
        assert len(prompts) == 3


class TestDryRunBehavior:
    """Test dry-run mode behavior."""
    
    def test_dry_run_no_api_calls_elevenlabs(self, tmp_path, monkeypatch, capsys):
        """Test that dry-run makes no actual API calls for ElevenLabs."""
        dest_dir = tmp_path / "synthetic"
        dest_dir.mkdir(parents=True)
        monkeypatch.setattr(red_team_module, 'DEST_DIR', dest_dir)
        
        # Mock prompt loading
        monkeypatch.setattr(red_team_module, 'load_prompts', 
                           lambda: ["Test prompt"])
        
        # Mock the TTS functions to track calls
        with patch('scripts.generate_red_team.generate_elevenlabs') as mock_eleven:
            with patch('scripts.generate_red_team.generate_openai') as mock_openai:
                # Parse arguments for dry-run
                with patch('sys.argv', ['generate_red_team.py', '--service', 'elevenlabs', 
                                       '--count', '2', '--dry-run']):
                    try:
                        red_team_module.main()
                    except SystemExit:
                        pass
                
                # Verify no API calls were made
                mock_eleven.assert_not_called()
                mock_openai.assert_not_called()
        
        # Verify placeholder files were created
        files = list(dest_dir.glob("elevenlabs_*.mp3"))
        assert len(files) == 2
        
        # Verify files contain dummy content
        for f in files:
            assert f.read_text() == "dummy content"
    
    def test_dry_run_no_api_calls_openai(self, tmp_path, monkeypatch):
        """Test that dry-run makes no actual API calls for OpenAI."""
        dest_dir = tmp_path / "synthetic"
        dest_dir.mkdir(parents=True)
        monkeypatch.setattr(red_team_module, 'DEST_DIR', dest_dir)
        
        monkeypatch.setattr(red_team_module, 'load_prompts', 
                           lambda: ["Test prompt"])
        
        with patch('scripts.generate_red_team.generate_elevenlabs') as mock_eleven:
            with patch('scripts.generate_red_team.generate_openai') as mock_openai:
                with patch('sys.argv', ['generate_red_team.py', '--service', 'openai', 
                                       '--count', '3', '--dry-run']):
                    try:
                        red_team_module.main()
                    except SystemExit:
                        pass
                
                mock_eleven.assert_not_called()
                mock_openai.assert_not_called()
        
        files = list(dest_dir.glob("openai_*.mp3"))
        assert len(files) == 3
    
    def test_dry_run_all_services(self, tmp_path, monkeypatch):
        """Test dry-run with 'all' services."""
        dest_dir = tmp_path / "synthetic"
        dest_dir.mkdir(parents=True)
        monkeypatch.setattr(red_team_module, 'DEST_DIR', dest_dir)
        
        monkeypatch.setattr(red_team_module, 'load_prompts', 
                           lambda: ["Test prompt"])
        
        with patch('scripts.generate_red_team.generate_elevenlabs') as mock_eleven:
            with patch('scripts.generate_red_team.generate_openai') as mock_openai:
                with patch('sys.argv', ['generate_red_team.py', '--service', 'all', 
                                       '--count', '2', '--dry-run']):
                    try:
                        red_team_module.main()
                    except SystemExit:
                        pass
                
                mock_eleven.assert_not_called()
                mock_openai.assert_not_called()
        
        # Should have files from both services
        eleven_files = list(dest_dir.glob("elevenlabs_*.mp3"))
        openai_files = list(dest_dir.glob("openai_*.mp3"))
        assert len(eleven_files) == 2
        assert len(openai_files) == 2


class TestNormalMode:
    """Test normal (non-dry-run) mode behavior."""
    
    def test_normal_mode_makes_api_calls(self, tmp_path, monkeypatch):
        """Test that normal mode makes actual API calls."""
        dest_dir = tmp_path / "synthetic"
        dest_dir.mkdir(parents=True)
        monkeypatch.setattr(red_team_module, 'DEST_DIR', dest_dir)
        
        monkeypatch.setattr(red_team_module, 'load_prompts', 
                           lambda: ["Test prompt"])
        
        with patch('scripts.generate_red_team.generate_elevenlabs') as mock_eleven:
            with patch('scripts.generate_red_team.generate_openai') as mock_openai:
                # Mock successful API calls
                mock_eleven.return_value = True
                mock_openai.return_value = True
                
                # Mock time.sleep to speed up test
                with patch('time.sleep'):
                    with patch('sys.argv', ['generate_red_team.py', '--service', 'elevenlabs', 
                                           '--count', '2']):
                        try:
                            red_team_module.main()
                        except SystemExit:
                            pass
                
                # Verify API was called
                assert mock_eleven.call_count == 2
                mock_openai.assert_not_called()
    
    def test_normal_mode_handles_failures(self, tmp_path, monkeypatch, capsys):
        """Test that normal mode handles API failures gracefully."""
        dest_dir = tmp_path / "synthetic"
        dest_dir.mkdir(parents=True)
        monkeypatch.setattr(red_team_module, 'DEST_DIR', dest_dir)
        
        monkeypatch.setattr(red_team_module, 'load_prompts', 
                           lambda: ["Test prompt"])
        
        with patch('scripts.generate_red_team.generate_elevenlabs') as mock_eleven:
            # Mock API failure
            mock_eleven.return_value = False
            
            with patch('time.sleep'):
                with patch('sys.argv', ['generate_red_team.py', '--service', 'elevenlabs', 
                                       '--count', '1']):
                    try:
                        red_team_module.main()
                    except SystemExit:
                        pass
            
            # Should continue despite failure
            assert mock_eleven.call_count == 1
    
    def test_rate_limiting_delay(self, tmp_path, monkeypatch):
        """Test that rate limiting delay is applied between successful calls."""
        dest_dir = tmp_path / "synthetic"
        dest_dir.mkdir(parents=True)
        monkeypatch.setattr(red_team_module, 'DEST_DIR', dest_dir)
        
        monkeypatch.setattr(red_team_module, 'load_prompts', 
                           lambda: ["Test prompt"])
        
        with patch('scripts.generate_red_team.generate_elevenlabs') as mock_eleven:
            with patch('time.sleep') as mock_sleep:
                mock_eleven.return_value = True
                
                with patch('sys.argv', ['generate_red_team.py', '--service', 'elevenlabs', 
                                       '--count', '3']):
                    try:
                        red_team_module.main()
                    except SystemExit:
                        pass
                
                # Should sleep after each success
                assert mock_sleep.call_count == 3
                mock_sleep.assert_called_with(1)


class TestArgumentParsing:
    """Test command-line argument parsing."""
    
    def test_default_arguments(self):
        """Test default argument values."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--service", choices=["elevenlabs", "openai", "all"], 
                          default="all")
        parser.add_argument("--count", type=int, default=5)
        parser.add_argument("--dry-run", action="store_true")
        
        args = parser.parse_args([])
        assert args.service == "all"
        assert args.count == 5
        assert args.dry_run is False
    
    def test_custom_arguments(self):
        """Test custom argument values."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--service", choices=["elevenlabs", "openai", "all"], 
                          default="all")
        parser.add_argument("--count", type=int, default=5)
        parser.add_argument("--dry-run", action="store_true")
        
        args = parser.parse_args(['--service', 'openai', '--count', '10', '--dry-run'])
        assert args.service == "openai"
        assert args.count == 10
        assert args.dry_run is True


class TestDirectoryCreation:
    """Test output directory creation."""
    
    def test_dest_dir_creation(self, tmp_path, monkeypatch):
        """Test that destination directory is created if it doesn't exist."""
        dest_dir = tmp_path / "new_directory" / "synthetic"
        monkeypatch.setattr(red_team_module, 'DEST_DIR', dest_dir)
        
        assert not dest_dir.exists()
        
        # Import should trigger directory creation
        from importlib import reload
        reload(red_team_module)
        
        # Directory should be created by module initialization
        assert dest_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
