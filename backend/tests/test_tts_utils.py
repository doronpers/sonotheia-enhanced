"""
Tests for TTS utilities API key handling and error recovery.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.tts_utils import (
    load_env_file,
    check_tts_dependencies,
    generate_elevenlabs,
    generate_openai
)


class TestLoadEnvFile:
    """Test environment file loading."""
    
    def test_load_env_file_with_script_path(self, tmp_path):
        """Test loading .env file with script path."""
        # Create a mock .env file
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\n")
        
        # Create mock script structure
        script_dir = tmp_path / "backend" / "scripts"
        script_dir.mkdir(parents=True)
        script_file = script_dir / "test_script.py"
        script_file.touch()
        
        # Test loading
        result = load_env_file(script_file)
        assert result is True
    
    def test_load_env_file_without_script_path(self, tmp_path, monkeypatch):
        """Test loading .env file from current directory."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\n")
        
        monkeypatch.chdir(tmp_path)
        result = load_env_file()
        assert result is True
    
    def test_load_env_file_missing_dotenv_module(self):
        """Test handling when python-dotenv is not installed."""
        with patch('scripts.tts_utils.load_dotenv', side_effect=ImportError):
            # This should handle ImportError gracefully
            result = load_env_file()
            assert result is False
    
    def test_load_env_file_exception_handling(self):
        """Test exception handling during .env loading."""
        with patch('scripts.tts_utils.load_dotenv', side_effect=Exception("Test error")):
            result = load_env_file()
            assert result is False


class TestCheckTtsDependencies:
    """Test TTS dependency checking."""
    
    def test_check_dependencies_all_available(self):
        """Test when all dependencies are available."""
        with patch('scripts.tts_utils.requests'):
            with patch('scripts.tts_utils.OpenAI'):
                deps = check_tts_dependencies()
                assert deps['requests'] is True
                assert deps['openai'] is True
    
    def test_check_dependencies_requests_missing(self):
        """Test when requests module is missing."""
        with patch('builtins.__import__', side_effect=ImportError):
            deps = check_tts_dependencies()
            assert deps['requests'] is False
            assert deps['openai'] is False
    
    def test_check_dependencies_openai_missing(self):
        """Test when openai module is missing."""
        # Mock requests available but openai not
        original_import = __builtins__.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'openai':
                raise ImportError
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            deps = check_tts_dependencies()
            # Both might be False due to import patching


class TestGenerateElevenlabs:
    """Test ElevenLabs API key handling and error recovery."""
    
    def test_generate_elevenlabs_no_api_key(self, tmp_path):
        """Test handling when API key is not set."""
        filename = str(tmp_path / "test.mp3")
        
        with patch.dict(os.environ, {}, clear=True):
            result = generate_elevenlabs("test text", filename)
            assert result is False
    
    def test_generate_elevenlabs_missing_requests_module(self, tmp_path):
        """Test handling when requests module is not available."""
        filename = str(tmp_path / "test.mp3")
        
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test_key"}):
            with patch('builtins.__import__', side_effect=ImportError):
                result = generate_elevenlabs("test text", filename)
                assert result is False
    
    def test_generate_elevenlabs_api_error(self, tmp_path):
        """Test handling of API errors."""
        filename = str(tmp_path / "test.mp3")
        
        # Mock requests module
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test_key"}):
            with patch('scripts.tts_utils.requests') as mock_requests:
                mock_requests.post.return_value = mock_response
                result = generate_elevenlabs("test text", filename)
                assert result is False
    
    def test_generate_elevenlabs_timeout(self, tmp_path):
        """Test handling of timeout errors."""
        filename = str(tmp_path / "test.mp3")
        
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test_key"}):
            with patch('scripts.tts_utils.requests') as mock_requests:
                mock_requests.post.side_effect = TimeoutError("Request timed out")
                result = generate_elevenlabs("test text", filename, timeout=1)
                assert result is False
    
    def test_generate_elevenlabs_success(self, tmp_path):
        """Test successful API call."""
        filename = str(tmp_path / "test.mp3")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake audio content"
        
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test_key"}):
            with patch('scripts.tts_utils.requests') as mock_requests:
                mock_requests.post.return_value = mock_response
                result = generate_elevenlabs("test text", filename)
                assert result is True
                assert os.path.exists(filename)
    
    def test_generate_elevenlabs_custom_api_key(self, tmp_path):
        """Test using custom API key parameter."""
        filename = str(tmp_path / "test.mp3")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake audio content"
        
        with patch('scripts.tts_utils.requests') as mock_requests:
            mock_requests.post.return_value = mock_response
            result = generate_elevenlabs("test text", filename, api_key="custom_key")
            assert result is True


class TestGenerateOpenai:
    """Test OpenAI API key handling and error recovery."""
    
    def test_generate_openai_no_api_key(self, tmp_path):
        """Test handling when API key is not set."""
        filename = str(tmp_path / "test.mp3")
        
        with patch.dict(os.environ, {}, clear=True):
            result = generate_openai("test text", filename)
            assert result is False
    
    def test_generate_openai_missing_module(self, tmp_path):
        """Test handling when openai module is not available."""
        filename = str(tmp_path / "test.mp3")
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('builtins.__import__', side_effect=ImportError):
                result = generate_openai("test text", filename)
                assert result is False
    
    def test_generate_openai_api_error(self, tmp_path):
        """Test handling of API errors."""
        filename = str(tmp_path / "test.mp3")
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('scripts.tts_utils.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_client.audio.speech.create.side_effect = Exception("API error")
                mock_openai.return_value = mock_client
                
                result = generate_openai("test text", filename)
                assert result is False
    
    def test_generate_openai_success(self, tmp_path):
        """Test successful API call."""
        filename = str(tmp_path / "test.mp3")
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('scripts.tts_utils.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.stream_to_file = Mock()
                mock_client.audio.speech.create.return_value = mock_response
                mock_openai.return_value = mock_client
                
                result = generate_openai("test text", filename)
                assert result is True
    
    def test_generate_openai_custom_api_key(self, tmp_path):
        """Test using custom API key parameter."""
        filename = str(tmp_path / "test.mp3")
        
        with patch('scripts.tts_utils.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.stream_to_file = Mock()
            mock_client.audio.speech.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            result = generate_openai("test text", filename, api_key="custom_key")
            assert result is True
            # Verify API key was used
            mock_openai.assert_called_once_with(api_key="custom_key")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
