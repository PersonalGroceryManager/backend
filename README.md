# Backend - Flask

## Environmental Variables

These variables are neccessary for the app to work

- **MODE** - This can be `development`, `testing` or `production`. This dicatates
  which database to use

- **DATABASE_URL_DEV** - Development database URL. For ease of developing, use in memory database such as `sqlite:///./dev.db`

- **DATABASE_URL_TEST** - Testing database URL. For ease of testing, use in memory database such as `sqlite:///./dev.db`

- **DATABASE_URL_PROD** - Development database URL. This is stored in secret.

TODO:

1. Fix user registration and login "lost server connection" error. Can fix this by catching `MySQLdb.OperationalError` then re-do the operation
2. Issue: DATABASE IS LOCKED ERROR - Seems to be solved with prepool ping -NEVERMIND this has not been fixed
3. Add parameterization in test suite

```python
@pytest.mark.parametrize("book_id, status_code", [
  (1, 200),    # Valid book ID
  (999, 404),  # Non-existent book ID
])
def test_get_book_various_ids(book_id, status_code):
  url = f"https://run.mocky.io/v3/9b2fc100-4c56-473d-b488-323dfd26396c/books/{book_id}"
  response = requests.get(url)
  assert response.status_code == status_code
```

4. Grouping tests
5. Explore pytest report plugins for more insightful reports
