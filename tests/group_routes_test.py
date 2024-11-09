# tests/routes_test.py


def test_get_groups_when_none_exists(client):
    """
    Test getting any groups upon startup. No groups should be present so
    expecting a 404 error
    """
    response = client.get('/groups')
    assert response.status_code == 404
    assert 'No Content' in response.json['error']
    assert 'No groups available' in response.json['message']


def test_create_group(client):
    """Test creating a new group."""
    response = client.post('/groups', json={
        'group_name': 'Random Group',
        'description': 'A group for testing purposes.'
    })
    assert response.status_code == 201

def test_get_groups(client):
    """Test getting all groups."""
    # Create a group to populate the database
    test_create_group(client)
    
    # Delete the newly created group
    response = client.get('/groups')
    assert response.status_code == 200


def test_delete_group(client):
    """Test deletion of a group."""
    # Create a group to populate the database
    test_create_group(client)

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
