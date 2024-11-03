# tests/routes_test.py

import pytest
from flask import Flask
from src.run import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client  # This is where the testing happens


def test_get_groups(client):
    """Test getting all groups."""
    response = client.get('/groups/get-all')
    assert response.status_code == 200
    assert isinstance(response.json, list)  # Check if response is a list


def test_create_group(client):
    """Test creating a new group."""
    response = client.post('/groups/create', json={
        'group_name': 'Random Group',
        'description': 'A group for testing purposes.'
    })
    assert response.status_code == 201
    assert response.json['status'] == 'success'


def test_delete_group(client):
    """Test deletion of a group."""
    response = client.delete('/groups/delete', json={
        'group_name': 'Random Group',
    })
    assert response.status_code == 204


def test_create_group_without_name(client):
    """Test creating a group without a name."""
    response = client.post('/groups/create', json={
        'description': 'Missing group name.'
    })
    assert response.status_code == 400
    assert 'Group name is required!' in response.json['message']

# Additional tests for other routes...
