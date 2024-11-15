from pathlib import Path

# Path to directory where test files are stored
files_dir = Path(__file__).parent / "static_files"


def test_file_exists():
    """
    Check if any receipts exists
    """
    if not any(file.is_file() for file in files_dir.iterdir()):
        raise IndexError
    
def test_add_receipt_to_group(client):
    
    # # Create a group with name 'Random Group'
    """Test creating a new group."""
    response = client.post('/groups', json={
        'group_name': 'Random Group',
        'description': 'A group for testing purposes.'
    })
    assert response.status_code == 201
    
    # Iterate across all files in receipt directory
    for file_path in files_dir.iterdir():
                
        # Ensure it is a file, not a directory
        if file_path.is_file():
            
            filename = file_path.name
            
            # Open the file in binary mode for uploading
            with open(file_path, 'rb') as test_file:
            
                # Add receipt to the newly created group with group ID = 1
                response = client.post(
                    "groups/1/receipts",
                    data={"file": (test_file, filename)},
                    content_type="multipart/form-data")
                
                assert response.status_code == 201


def test_add_receipt_to_non_existing_group(client):

    # Iterate across all files in receipt directory
    for file_path in files_dir.iterdir():
                
        # Ensure it is a file, not a directory
        if file_path.is_file():
            
            filename = file_path.name
            
            # Open the file in binary mode for uploading
            with open(file_path, 'rb') as test_file:
            
                # Add receipt to the newly created group with group ID = 1
                response = client.post(
                    "groups/1/receipts",
                    data={"file": (test_file, filename)},
                    content_type="multipart/form-data")
                
                # Expect a Not Found Error since no group to add receipt to
                assert response.status_code == 404

def test_get_receipt_from_group(client):
    
    test_add_receipt_to_group(client)
    
    response = client.get('groups/1/receipts')
    # get_json() can only be called once as it consumes data - store it
    data = response.get_json()  
    
    assert response.status_code == 200
    assert "receipts" in data
    assert isinstance(data["receipts"], list) == True
    