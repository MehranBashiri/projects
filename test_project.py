import pytest
from unittest.mock import patch
from io import StringIO
import json
import os  # Added for file cleanup
from modes import calculate_mode_details, calculate_route_preferences, summarize_alternatives
from inputs_handler import load_relatives, get_user_preferences, InvalidInputError
from routes import calculate_distance

# ----------------------------- Fixtures -----------------------------

@pytest.fixture(scope="session", autouse=True)
def clean_logs_and_reports():
    """Session-wide fixture to clean logs and reports before running tests."""
    log_file = "test.log"
    report_file = "report.html"
    files_to_clean = [log_file, report_file]
    for file in files_to_clean:
        if os.path.exists(file):
            with open(file, "w"):  # Truncate the file to clear old data
                pass

@pytest.fixture
def transport_modes():
    """Fixture for transport modes."""
    return [
        {"mode": "Bus", "speed_kmh": 40, "cost_per_km": 2, "transfer_time_min": 5},
        {"mode": "Train", "speed_kmh": 80, "cost_per_km": 5, "transfer_time_min": 2},
        {"mode": "Walking", "speed_kmh": 5, "cost_per_km": 0, "transfer_time_min": 0},
        {"mode": "Bicycle", "speed_kmh": 15, "cost_per_km": 0, "transfer_time_min": 1}
    ]

@pytest.fixture
def sample_distances():
    """Fixture for distances between nodes."""
    return {("A", "B"): 10, ("B", "C"): 5, ("C", "D"): 15}

@pytest.fixture
def sample_route():
    """Fixture for a sample route."""
    return ["A", "B", "C", "D"]

@pytest.fixture
def sample_relatives():
    """Fixture for mock relative data."""
    return [
        {"Relative_number": "Relative_1", "name": "Gangnam-daero", "district": "Gangnam-gu", "latitude": 37.4979, "longitude": 127.0276},
        {"Relative_number": "Relative_2", "name": "Yangjae-daero", "district": "Seocho-gu", "latitude": 37.4833, "longitude": 127.0322},
        {"Relative_number": "Relative_3", "name": "Sinsa-daero", "district": "Gangnam-gu", "latitude": 37.5172, "longitude": 127.0286}
    ]

# ------------------------- Tests for `modes.py` ----------------------

@pytest.mark.parametrize("distance, expected_time", [
    (10, 15.0),  # 10 km
    (20, 30.0),  # 20 km
    (5, 7.5)     # 5 km
])
def test_calculate_mode_details_valid(transport_modes, distance, expected_time):
    """Test calculating mode details for a valid route and transport modes."""
    from_node, to_node = "A", "B"  # 10 km
    mode_details = calculate_mode_details(from_node, to_node, distance, transport_modes)
    
    assert isinstance(mode_details, list)
    assert len(mode_details) == len(transport_modes)
    
    # Validate Bus details
    bus_details = mode_details[0]
    assert bus_details["mode"] == "Bus"
    assert bus_details["travel_time"] == pytest.approx(expected_time, rel=1e-2)  # 15 minutes
    assert bus_details["total_time"] == pytest.approx(expected_time + 5, rel=1e-2)  # Travel + transfer time

def test_calculate_mode_details_missing_key():
    """Test if missing key in mode data raises a KeyError."""
    incomplete_modes = [{"mode": "Bus", "speed_kmh": 40, "cost_per_km": 2}]  # Missing transfer_time_min
    from_node, to_node, distance = "A", "B", 10
    
    with pytest.raises(KeyError):
        calculate_mode_details(from_node, to_node, distance, incomplete_modes)

def test_calculate_route_preferences_valid(sample_route, sample_distances, transport_modes):
    """Test route preference calculation using the balanced_topsis method."""
    route_preferences = calculate_route_preferences(sample_route, sample_distances, transport_modes, "balanced_topsis")
    
    assert isinstance(route_preferences, list)
    assert len(route_preferences) > 0  # Alternatives should exist
    assert len(route_preferences[0]) == len(sample_route) - 1  # One preference per segment

def test_calculate_route_preferences_invalid_preference(sample_route, sample_distances, transport_modes):
    """Test that an invalid preference raises a ValueError."""
    with pytest.raises(ValueError):
        calculate_route_preferences(sample_route, sample_distances, transport_modes, "invalid_preference")

# ---------------------------- Tests for `summarize_alternatives` ------------------------

def test_summarize_alternatives():
    """Test that the summarize_alternatives function works as expected."""
    route_alternatives = [
        [
            {"from": "A", "to": "B", "distance": 10, "selected_mode": {"mode": "Bus", "cost": 20, "total_time": 15}},
            {"from": "B", "to": "C", "distance": 5, "selected_mode": {"mode": "Train", "cost": 25, "total_time": 10}},
        ]
    ]
    summaries = summarize_alternatives(route_alternatives)
    
    assert isinstance(summaries, list)
    assert len(summaries) == 1
    assert "Alternative 1" in summaries[0]["Alternative"]

def test_summarize_alternatives_empty():
    """Test if empty alternatives return an empty summary."""
    summaries = summarize_alternatives([])
    assert summaries == []

# ------------------------ Tests for `inputs_handler.py` ------------------------

def test_load_relatives_valid(sample_relatives):
    """Test loading relatives from a valid JSON file."""
    mock_file = StringIO(json.dumps(sample_relatives))
    with patch("builtins.open", return_value=mock_file):
        relatives = load_relatives("data/relatives.json")
        assert isinstance(relatives, list)
        assert len(relatives) == len(sample_relatives)

def test_load_relatives_invalid_file():
    """Test if loading a non-existent file raises a FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_relatives("invalid_path.json")

def test_invalid_user_input():
    """Test handling of invalid user input for preferences."""
    with patch("builtins.input", return_value="4"):  # Simulate an invalid input choice
        with pytest.raises(InvalidInputError):
            get_user_preferences()

# ---------------------------- Tests for `routes.py` --------------------------

def test_calculate_distance():
    """Test the distance calculation function with valid coordinates."""
    point1, point2 = (37.4979, 127.0276), (37.4833, 127.0322)
    distance = calculate_distance(point1, point2)
    
    assert isinstance(distance, float)
    assert 0 < distance < 2  # Validate realistic range for coordinates

def test_calculate_distance_zero_distance():
    """Test the distance calculation with zero distance."""
    point1 = point2 = (37.4979, 127.0276)
    distance = calculate_distance(point1, point2)
    
    assert distance == 0

# ----------------------- Entry point for running tests ------------------------

if __name__ == "__main__":
    pytest.main(["-v", "--html=report.html", "--self-contained-html"])
