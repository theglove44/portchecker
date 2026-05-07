"""Tests for config module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from portchecker import config


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_config_dir = config.CONFIG_DIR
        original_config_file = config.CONFIG_FILE
        original_favorites_file = config.FAVORITES_FILE
        
        config.CONFIG_DIR = Path(tmpdir)
        config.CONFIG_FILE = config.CONFIG_DIR / "config.json"
        config.FAVORITES_FILE = config.CONFIG_DIR / "favorites.json"
        
        yield tmpdir
        
        # Restore original paths
        config.CONFIG_DIR = original_config_dir
        config.CONFIG_FILE = original_config_file
        config.FAVORITES_FILE = original_favorites_file


def test_ensure_config_dir(temp_config_dir):
    """Test config directory creation."""
    config.ensure_config_dir()
    assert config.CONFIG_DIR.exists()


def test_load_save_config(temp_config_dir):
    """Test loading and saving config."""
    test_config = {"cli_path": "/usr/local/bin/portchecker", "show_system": True}
    
    config.save_config(test_config)
    loaded = config.load_config()
    
    assert loaded == test_config


def test_load_favorites_empty(temp_config_dir):
    """Test loading favorites when file doesn't exist."""
    favorites = config.load_favorites()
    assert favorites == []


def test_save_load_favorites(temp_config_dir):
    """Test saving and loading favorites."""
    test_favorites = [
        {"port": 3000, "name": "Frontend", "note": "React dev server"},
        {"port": 8080, "name": "Backend", "note": "API server"},
    ]
    
    config.save_favorites(test_favorites)
    loaded = config.load_favorites()
    
    assert loaded == test_favorites


def test_add_favorite(temp_config_dir):
    """Test adding a favorite."""
    result = config.add_favorite(3000, "Frontend", "React app")
    assert result is True
    
    favorites = config.load_favorites()
    assert len(favorites) == 1
    assert favorites[0]["port"] == 3000
    assert favorites[0]["name"] == "Frontend"
    assert favorites[0]["note"] == "React app"


def test_add_duplicate_favorite(temp_config_dir):
    """Test adding a duplicate favorite returns False."""
    config.add_favorite(3000, "Frontend")
    result = config.add_favorite(3000, "Different Name")
    
    assert result is False
    favorites = config.load_favorites()
    assert len(favorites) == 1


def test_remove_favorite_by_port(temp_config_dir):
    """Test removing a favorite by port number."""
    config.add_favorite(3000, "Frontend")
    config.add_favorite(8080, "Backend")
    
    result = config.remove_favorite("3000")
    
    assert result is True
    favorites = config.load_favorites()
    assert len(favorites) == 1
    assert favorites[0]["port"] == 8080


def test_remove_favorite_by_name(temp_config_dir):
    """Test removing a favorite by name."""
    config.add_favorite(3000, "Frontend")
    config.add_favorite(8080, "Backend")
    
    result = config.remove_favorite("frontend")  # Case insensitive
    
    assert result is True
    favorites = config.load_favorites()
    assert len(favorites) == 1


def test_remove_nonexistent_favorite(temp_config_dir):
    """Test removing a favorite that doesn't exist."""
    result = config.remove_favorite("9999")
    assert result is False


def test_get_favorite_by_name(temp_config_dir):
    """Test getting a favorite by name."""
    config.add_favorite(3000, "Frontend", "React")
    
    fav = config.get_favorite_by_name("Frontend")
    assert fav is not None
    assert fav["port"] == 3000
    
    # Case insensitive
    fav2 = config.get_favorite_by_name("frontend")
    assert fav2 is not None


def test_get_favorite_by_name_not_found(temp_config_dir):
    """Test getting a non-existent favorite."""
    fav = config.get_favorite_by_name("NonExistent")
    assert fav is None
