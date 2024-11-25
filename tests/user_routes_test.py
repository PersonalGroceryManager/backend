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
    # Create/register a user
    response = client.post('/users', json={
        'username': f'Test Username',
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 201
    
    # Authenticate the user with the same username and password and JWT
    response = client.post(
        'users/login', 
        json={'username': 'Test Username',
              'password': 'Test Password'
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
    # Create/register a user
    response = client.post('/users', json={
        'username': 'Test Username',
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 201
    
    # Attempt to get the User ID, username and email without JWT
    response = client.get('/users')
    assert response.status_code == 401


def test_get_user_info_authorized(client):
    """
    Test the route to obtain user information
    """
    # Create/register a user
    response = client.post('/users', json={
        'username': 'Test Username',
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 201
    
    # Authenticate the user with the same username and password and JWT
    response = client.post(
        'users/login', 
        json={'username': 'Test Username',
              'password': 'Test Password'
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
    user_id = data.get('user_id')
    username = data.get('username')
    email = data.get('email')
    assert user_id == 1
    assert username == 'Test Username'
    assert email == 'test@email.com'


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
    # Create/register a user
    response = client.post('/users', json={
        'username': 'Test Username',
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 201
    
    # Duplicate creation should result in resource conflict
    response = client.post('/users', json={
        'username': 'Test Username',
        'password': 'Test Password 2',
        'email': 'test@email.com'
    })
    assert response.status_code == 409
    

def test_delete_user(client):
    """
    Test the route to delete a user.
    """
    # Create/register a user
    response = client.post('/users', json={
        'username': 'Test Username',
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 201
    
    # Authenticate the user with the same username and password and JWT
    response = client.post(
        'users/login', 
        json={'username': 'Test Username',
              'password': 'Test Password'
              })
    assert response.status_code == 200
    
    # Extract JWT  
    token = response.get_json()["access_token"]
    
    # Delete the user by its username
    response = client.delete(
        '/users', 
        json={
            'username': 'Test Username'
            },
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204


def test_get_user_id(client):
    
    test_username = 'Test Username'
    
    # Create/register a user
    response = client.post('/users', json={
        'username': f'{test_username}',
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 201
    
    response = client.get(f'users/resolve/{test_username}')
    assert response.status_code == 200

    # Verify user ID = 1 (newly created)
    data = response.get_json()
    user_id = data.get('user_id')
    assert user_id == 1


def test_get_username(client):
    
    test_username = 'Test Username'
    
    # Create/register a user
    response = client.post('/users', json={
        'username': f'{test_username}',
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 201
    
    # The first user should have a user ID of 1
    response = client.get(f'users/resolve/1')
    assert response.status_code == 200

    # Verify username = Test Username (newly created)
    data = response.get_json()
    print(data)
    username = data.get('username')
    assert username == test_username
    