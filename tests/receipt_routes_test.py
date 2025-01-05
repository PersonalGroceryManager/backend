from pathlib import Path

# Path to directory where test files are stored
files_dir = Path(__file__).parent / "static_files"


def test_file_exists():
    """
    Check if any receipts exists
    """
    if not any(file.is_file() for file in files_dir.iterdir()):
        raise IndexError
    
# Files that correspond to receipts pre-seeded in database (for group 
# "Example Group" only)
uploaded_receipts_file_names = ["april_4_2024.pdf", "april_25_2024.pdf"]
    
def test_add_new_receipt_to_group(client):
    """
    Add new receipts to the group "Example Group". This action should return
    a 401 - Resource created status code
    """
    
    # Iterate across all files in receipt directory
    for file_path in files_dir.iterdir():
                
        # Ensure it is a file, not a directory
        if file_path.is_file():
            
            filename = file_path.name\
            
            # If these receipts are previously uploaded, skip it
            if filename in uploaded_receipts_file_names:
                continue
            
            # Open the file in binary mode for uploading
            with open(file_path, 'rb') as test_file:
            
                # Add receipt to the pre-seeded group with group ID = 1
                response = client.post(
                    "groups/1/receipts",
                    data={"file": (test_file, filename)},
                    content_type="multipart/form-data")
                
                assert response.status_code == 201
                
def test_add_existing_receipt_to_group(client):
    """
    Attempt to add existing receipts to "Example Group". This action should 
    return a 409 - Resource Already Exists error
    """
    
    # Iterate across all files in receipt directory
    for file_path in files_dir.iterdir():
                
        # Ensure it is a file, not a directory
        if file_path.is_file():
            
            filename = file_path.name
            
            # If these receipts are new, skip it
            if filename not in uploaded_receipts_file_names:
                continue
            
            # Open the file in binary mode for uploading
            with open(file_path, 'rb') as test_file:
            
                # Add receipt to the pre-seeded group with group ID = 1
                response = client.post(
                    "groups/1/receipts",
                    data={"file": (test_file, filename)},
                    content_type="multipart/form-data")
                
                assert response.status_code == 409

def test_add_receipt_to_non_existing_group(client):
    """
    Attempt to add receipts to a new group that does not exist. This action
    should return a 404 error.
    """

    # Iterate across all files in receipt directory
    paths_in_dir = files_dir.iterdir()
    file_paths = [path for path in paths_in_dir if path.is_file()]

    # Attempt to add the first file as a receipt to a non-existing group
    with open(file_paths[0], 'rb') as test_file:

            # Attempt to add receipt to a non-existing group with ID 10000
            response = client.post(
                "groups/10000/receipts",
                data={"file": (file_paths[0], file_paths[0].name)},
                content_type="multipart/form-data")
            
            # Expect a Not Found Error since no group to add receipt to
            assert response.status_code == 404

def test_get_receipt_from_group(client):
    """
    Get a list of receipts uploaded to the group with Group ID 1. Expects a
    list oof receipts.
    """
    
    response = client.get('groups/1/receipts')
    data = response.get_json()  
    
    assert response.status_code == 200
    assert "receipts" in data
    assert isinstance(data["receipts"], list) == True
    