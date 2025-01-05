def test_create_user(client):
    response = client.post('/users', json={
        'username': 'Test Username',
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 201


def test_login(client):
    """
    Test authentication by creating a user, logging in and viewing the returned
    JWT
    """
    # Authenticate the user with the same username and password and JWT
    response = client.post(
        'users/login', 
        json={"username": "Username1",
              "password": "Username1!"
              })
    assert response.status_code == 200
    
    # Verify existence of JWT token    
    response_content = response.get_json()
    assert "access_token" in response_content
    

def test_get_user_info_unauthorized(client):
    """
    Test the route to obtain user information by giving an invalid token.
    Expect an error 401 unauthorized
    """
    # Attempt to get the User ID, username and email without JWT
    response = client.get('/users')
    assert response.status_code == 401


def test_get_user_info_authorized(client):
    """
    Test the route to obtain user information
    """
    # Create/register a user
    response = client.post('/users', json={
        'username': 'Test Username 2',
        'password': 'Test Password 2',
        'email': 'test2@email.com'
    })
    assert response.status_code == 201
    
    # Authenticate the user with the same username and password and JWT
    response = client.post(
        'users/login', 
        json={'username': 'Test Username 2',
              'password': 'Test Password 2'
              })
    assert response.status_code == 200
    
    # Extract JWT  
    token = response.get_json()["access_token"]
    
    # Get the User ID, username and email
    response = client.get('/users', 
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # Verify that the same information was returned
    # Note: User ID should be 1 (first user in testing database)
    data = response.get_json()
    username = data.get('username')
    email = data.get('email')
    assert username == 'Test Username 2'
    assert email == 'test2@email.com'


def test_create_user_with_incomplete_fields(client):
    """
    Test the creation of users wiithout either username, password, or email.
    Expect error of status code 400 (Bad Request)
    """
    response = client.post('/users', json={
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 400

    response = client.post('/users', json={
        'username': 'Test Username',
        'email': 'test@email.com'
    })
    assert response.status_code == 400
    
    response = client.post('/users', json={
        'username': 'Test Username',
        'password': 'Test Password',
    })
    assert response.status_code == 400

    
def test_creating_duplicate_users(client):
    """
    Test the creation of duplicate users (users with the same usernames).
    Expect error of status code 409 (Resource Conflict)
    """
    # Create/register a user with a username that already exists
    response = client.post('/users', json={
        'username': 'Username1',
        'password': 'anything',
        'email': 'anything@email.com'
    })
    assert response.status_code == 409
    

def test_delete_user(client):
    """
    Test the route to delete a user.
    """
    # Create/register a user
    response = client.post('/users', json={
        'username': 'UsernameToDelete',
        'password': 'PasswordToDelete',
        'email': 'test@email.com'
    })
    assert response.status_code == 201
    
    # Authenticate the user with the same username and password and JWT
    response = client.post(
        'users/login', 
        json={'username': 'UsernameToDelete',
              'password': 'PasswordToDelete'
              })
    assert response.status_code == 200
    
    # Extract JWT  
    token = response.get_json()["access_token"]
    
    # Delete the user by its username
    response = client.delete(
        '/users', 
        json={
            'username': 'UsernameToDelete'
            },
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204


def test_get_user_id(client):
    
    test_username = "Username1"
    
    response = client.get(f'users/resolve/{test_username}')
    assert response.status_code == 200

    data = response.get_json()
    user_id = data.get('user_id')
    assert isinstance(user_id, int)
    assert user_id == 1  # According to the SQL file

def test_get_username(client):
    
    test_username = 'Username1'
    
    # The first user should have a user ID of 1
    response = client.get(f'users/resolve/1')
    assert response.status_code == 200

    # Verify username = Test Username (newly created)
    data = response.get_json()
    assert 'username' in data
    username = data.get('username')
    assert isinstance(username, str)
    assert username == test_username
