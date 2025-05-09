# Routes

This folder contains the code for all app routes. Routes should be categorized by function into files of appropriate name.

Routers are automatically loaded and imported via the `__init__.py` file. Using `from DataAPI.routes import ROUTERS` will gives a list, `ROUTERS`, of all routers defined in this directory. To conform to this automatic loading, you must create new routes files as defined in [Creating New Routes](#creating-new-routes).

This automatic loading of routes allows new routes to be created by only creating a single file. Additionaly, routes can still be imported manually, if desired; this automatic loading does not interfere with that.

## Creating New Routes

If your new desired routes fits within an existing category, add it there; otherwise, create a new route file.

1. First, create a new python file in this directory, naming it whatever you'd like
   - preferrably, the name should match what your new routes will do
2. Next, copy the following boilerplate code into the file:

   ```python
   from __future__ import annotations

   import logging
   from typing import Final

   from fastapi import APIRouter

   logger = logging.getLogger(__name__)

   _section_name: Final[str] = "{your_route_name}"

   # Do not change the name of "router"!
   router = APIRouter(prefix=f"/{_section_name}", tags=[_section_name])


   @router.get("/hello")
   def hello() -> str:
       return "hello, world!"
   ```

   This gives you a good starting point.

3. Change the name of the `_section_name` variable to something appropriate. This will be appended to the beginning of all routes in this file.
   - e.g., `@router.get("/hello")`, as shown in the example above, will actually be the route `/{your_route_name}/hello`
   - the goal of this behavior is to divide routes into sensible categories, akin to folders and subfolders in a filesystem

After following these steps, your routes will automatically be imported; you do not need to modify any other file for your routes to be added to the application.

## Bypass Automatic Loading

By default, any files starting with an underscore will be ignored by the automatic loading procedure.
