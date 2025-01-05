# tests/routes_test.py


def test_create_group(client):
    """Test creating a new group."""
    response = client.post('/groups', json={
        'group_name': 'Random Group',
        'description': 'A group for testing purposes.'
    })
    assert response.status_code == 201

def test_get_groups(client):
    """Test getting all groups."""
    # Get groups
    response = client.get('/groups')
    assert response.status_code == 200
    # TODO: Further assertions about group information
    data = response.json
    print(data)
    assert isinstance(data, list)
    assert "group_id" in data[0]
    assert "group_name" in data[0]
    assert "description" in data[0]
    assert data[0]["group_name"] == "Example Group"
    assert data[0]["description"] == "Example Description"


def test_delete_group(client):
    """Test deletion of a group."""
    # Delete the newly created group
    response = client.delete('/groups', json={
        'group_name': 'Random Group',
    })
    assert response.status_code == 204


def test_create_group_without_name(client):
    """
    Test creating a group without a name. Should return an error status code
    of 400 to indicate Bad Request
    """
    response = client.post('/groups', json={
        'description': 'Missing group name.'
    })
    assert response.status_code == 400
