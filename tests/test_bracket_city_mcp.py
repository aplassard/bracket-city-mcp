import pytest
from unittest.mock import patch, MagicMock

from src.bracket_city_mcp.main import mcp

@pytest.fixture
def client():
    return mcp.test_client()

@pytest.fixture
def mock_game_fixture():
    with patch('src.bracket_city_mcp.main.game', new_callable=MagicMock) as mock_g:
        yield mock_g

def test_health_check(client):
    response = client.tool("health")
    assert response.result == "OK"

def test_get_full_game_text(client, mock_game_fixture):
    mock_game_fixture.get_rendered_game_text.return_value = "Full game text"
    response = client.resource("bracketcity://game")
    assert response.result == "Full game text"
    mock_game_fixture.get_rendered_game_text.assert_called_once()

def test_get_clue_text_valid(client, mock_game_fixture):
    mock_game_fixture.get_rendered_clue_text.return_value = "Clue text for #C1#"
    response = client.resource("bracketcity://clue/#C1#")
    assert response.result == "Clue text for #C1#"
    mock_game_fixture.get_rendered_clue_text.assert_called_once_with("#C1#")

def test_get_clue_text_invalid(client, mock_game_fixture):
    mock_game_fixture.get_rendered_clue_text.side_effect = ValueError("Invalid clue ID")
    response = client.resource("bracketcity://clue/INVALID_CLUE_ID")
    assert "Invalid clue ID" in response.result
    mock_game_fixture.get_rendered_clue_text.assert_called_once_with("INVALID_CLUE_ID")

def test_get_available_clues(client, mock_game_fixture):
    mock_game_fixture.active_clues = {"#C1#", "#C2#"}
    response = client.resource("bracketcity://clues/available")
    assert isinstance(response.result, list)
    # For pytest, to compare lists ignoring order, it's common to sort them or use sets
    assert sorted(response.result) == sorted(["#C1#", "#C2#"])
