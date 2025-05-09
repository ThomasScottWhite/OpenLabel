# OpenLabel Backend

For information on how to run the app, see the [root README](../../README.md).

## API Documentation

With the app running, visit `{API_URL}/docs` for automatically generated API documentation. If you are using the default configuration settings, this link should work: <http://localhost:6969/docs>

Additionally, most functions have docstrings describing their function and parameters.

## Technologies

This API runs on Python (developed and tested using version 3.12) and uses [FastAPI](https://fastapi.tiangolo.com/) as its primary API framework/package. For our database, we chose to use [MongoDB](https://www.mongodb.com/).

### FastAPI

FastAPI is a performant, easy-to-use Python-based API framework. It was chosen both for its ease-of-use and several project member's familiarity with the framework.

One of its more useful features is its seemless integration of [Pydantic](https://docs.pydantic.dev/latest/), a popular Python data validation library. With FastAPI, data is automatically validated as requests are made; all you need to do is create a Pydantic model and use Python's built-in typehinting. Given that we chose an unstructured, document-based database in MongoDB, this seamless validation was essential to ensuring the validity of data.

FastAPI also supports automatically generated API documentation, which eliminated the need to manually alter API documentation when changes were made or new routes were added.

### MongoDB

We chose MongoDB due to it's flexibility as an unstructured database. The lack of structure puts more pressure on the backend to validate data, but allows us to store data in a more natural and varied format. Project members Thomas White and Harry Heitmeier stored annotations using a SQL database during their Co-op at Hunter Engineering and noted how suffocating the restrictive database structure was, especially when attempting to store data for various annotation types. Beyond that, adding new annotation styles is as easy as inserting into the database (and creating a corresponding Pydantic model for validation on the backend).

## File Structure

Information regarding the structure of our project.

- `db/`: contains all database-related code
  - for more info, [click here](./db/README.md)
- `routes/`: contains implementation/declaration of API routes, organized by routes supercategory (e.g., users, projects, files, etc.)
  - for more info, [click here](./routes/README.md)
- `__main__.py`: The entrypoint to our app; is what's run when using `python -m DataAPI` (see main project )
- `app.py`: contains the declaration of our `FastAPI` app
  - separating this from `__main__.py` allows for more flexibility, such as importing our app without any starting logic
- `config.py`: contains/initializes configuration parameters using `pydantic-settings`, which auto-loads environment variables into a Pydantic model
  - with how Python works, modules act as singletons, which is how this file is intended to be treated
  - config values can be imported using `from DataAPI.config import CONFIG`
- `exceptions.py`: contains custom exceptions that allow us to differentiate between unintended errors and end user-based errors
- `models.py`: contains all the Pydantic models and enumerators used throughout the project.
- `test.py`: contains some test functions

## Contributing

Check the `README.md` in `/routes/` before you make new routes!

## Potential Improvements

- using asynchronous instead of synchronous access to the database
- batching file uploads/downloads
