# Backend - Flask

## Environmental Variables
These variables are neccessary for the app to work

* **MODE** - This can be `development`, `testing` or `production`. This dicatates
which database to use

* **DATABASE_URL_DEV** - Development database URL. For ease of developing, use in memory database such as `sqlite:///./dev.db`

* **DATABASE_URL_TEST** - Testing database URL. For ease of testing, use in memory database such as `sqlite:///./dev.db`

* **DATABASE_URL_PROD** - Development database URL. This is stored in secret.
