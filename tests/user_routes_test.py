import pytest


def test_create_user(client):
    response = client.post('/user/create', json={
        'username': 'Test Username',
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 200


def test_get_user_info(client):
    # Get user ID
    response = client.get('user/get/user-id/Test Username')
    assert response.status_code == 200

    # User ID should be 1 (first user in testing database)
    data = response.get_json()
    user_id = data.get('user_id')
    assert user_id == 1


def test_get_username(client):
    response = client.get('user/get/username/1')
    assert response.status_code == 200

    data = response.get_json()
    username = data.get('username')
    assert username == 'Test Username'


def test_get_user_email(client):
    response = client.get('user/get/email/1')
    assert response.status_code == 200

    data = response.get_json()
    email = data.get('email')
    assert email == 'test@email.com'


def test_login(client):
    response = client.post('user/login', json={
        'username': 'Test Username',
        'password': 'Test Password'
    })
    assert response.status_code == 200


def test_get_all_users(client):
    response = client.get('/user/get-all')
    assert response.status_code == 200


def test_delete_user(client):
    response = client.delete('/user/delete', json={
        'user_id': 1
    })
    assert response.status_code == 200
