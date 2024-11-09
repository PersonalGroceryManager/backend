def test_create_user(client):
    response = client.post('/users', json={
        'username': 'Test Username',
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 201

    
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
    
    # Delete the user by its username
    response = client.delete('/users', json={
        'username': 'Test Username'
    })
    assert response.status_code == 204


def test_get_user_info(client):
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
    
    # Get the User ID, username and email
    response = client.get('users/1')
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


def test_login(client):
    
    # Create/register a user
    response = client.post('/users', json={
        'username': f'Test Username',
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 201
    
    # Authenticate the user with the same username and password
    response = client.post('users/login', json={
        'username': 'Test Username',
        'password': 'Test Password'
    })
    assert response.status_code == 200


def test_delete_user(client):
    
    # Create/register a user
    response = client.post('/users', json={
        'username': f'Test Username',
        'password': 'Test Password',
        'email': 'test@email.com'
    })
    assert response.status_code == 201
    
    # Delete the user (user_id = 1 since first user)
    response = client.delete('/users', json={
        'user_id': 1
    })
    assert response.status_code == 204
