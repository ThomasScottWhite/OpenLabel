# DataAPI Database

This folder contains all the logic the backend uses to interact with the [MongoDB](https://www.mongodb.com) database. MongoDB was chosen for its flexible, unstructured data, which is well-suited to the many annotation forms available and further extension.

## Database Structure

MongoDB is not a relational database, so there is no pre-defined structure; however, we have a structure that we follow. This structure is enforced primarily by our Pydantic models defined in [`DataAPI/models.py`](../models.py). A summary of this structure is below.

MongoDB organizes documents using _collections_; the subheadings below each represent one of those collections as they appear in the database (which may not necessarily match what is presented to users). Additionally, when there are sub-interfaces/structures defined below, they are stored within the same collection as their super-interfaces or sibling-interfaces. MongoDB is unstructured, so there is no issue with storing them together, which allows us to have flexible and inheritence-like behavior without the use of many tables or null values.

### `roles`

Each document in `roles` is formatted like the following (using TypeScript interface notation):

```typescript
interface Role {
  _id: ObjectId; // the role's ID (auto-generated by MongoDB)
  name: string; // the name of the role
  permissions: {
    // the permissions of the role
    resource: string; // the name of the resource the permission corresponds to
    actions: string[]; // the actions this role can take on the resource (read, write, update, delete)
  }[];
  description: string; // a short description of the role
}
```

### `users`

Each document in `users` is formatted like the following (using TypeScript interface notation):

```typescript
interface User {
  _id: ObjectId; // the role's ID (auto-generated by MongoDB)
  username: string; // the user's custom username; must be unique
  email: string; // the user's email they want associated to their account; must be unique
  password: string; // the user's HASHED password
  firstName: string; // the user's real first name
  lastName: string; // the user's real last name
  roleId: ObjectId; // the ID of the role in the roles collection the user is assigned
  isActive: boolean; // whether the user is active
  lastLogin: Date; // the timestamp of the user's last login
}
```

### `projects`

Each document in `projects` is formatted like the following (using TypeScript interface notation):

```typescript
interface Project {
  _id: ObjectId; // the project's ID (auto-generated by MongoDB)
  name: string; // the name of the project
  description: string; // the description of the project
  createdBy: ObjectId; // the ID of the user who created the project
  createdAt: Date; // the timestamp when the project was createad
  updatedAt: Date; // the timestamp of the project's last update (to its parameters)
  members: {
    // the users that are part of the project
    userId: ObjectId; // the user ID of the member
    roleId: ObjectId; // the ID of the role the user has within the project
  }[];
  settings: {
    dataType: string; // the data type used by the project (e.g., text, image)
    annotationType: string; // the type of annotations being used in the project (e.g., classification)
    isPublic: boolean; // whether the project is publically visible
    labels: string[]; // the labels/classes the project uses
  };
}
```

### `annotations`

Each document in `annotations` is formatted like one of the following (using TypeScript interface notation):

```typescript
interface BaseAnnotation {
  _id: ObjectId; // the annotation's ID (auto-generated by MongoDB)
  type: string; // the annotation type (e.g., classfication, object-detection)
  label: string; // the annotation's label/class
  confidence: number; // the percent confidence that the annotation is correct; should be a real number in the interval [0, 1]
  createdBy: ObjectId; // the ID of the user who created the annotation
  createdAt: Date; // the timestamp when the annotation was createad
  updatedAt: Date; // the timestamp of the annotation's last update (to its parameters)
  fileId: ObjectId; // the ID of the file this annotation corresponds to
  projectId: ObjectId; // the ID of the project this annotation corresponds to
}
```

For classification annotations, nothing is added to the base annotation, though we know the `type` is `"classification"`.

```typescript
interface ClassificationAnnotation extends BaseAnnotation {
  type: "classification";
}
```

The other annotations types follow suit:

```typescript
interface ObjectDetection extends BaseAnnotation {
  type: "object-detection";
  bbox: {
    x: number; // the x-coordinate of the bounding box's center as a proportion/percentage of the image width
    y: number; // the y-coordinate of the bounding box's center as a proportion/percentage of the image height
    width: number; // the width of the bounding box as a proportion/percentage of the image width
    height: number; // the height of the bounding box as a proportion/percentage of the image height
  };
}
```

### File Storage

The file storage collections are interesting as they are automatically determined using MongoDB's pre-made [GridFS](https://www.mongodb.com/docs/manual/core/gridfs/) file storage method. Excluding how GridFS works under the hood, the associated metadata we store about a file is as follows:

```typescript
interface FileMeta {
  _id: ObjectId; // the ID of the file (auto-generated by MongoDB)
  createdBy: ObjectId; // the ID of the user who uploaded the image
  createdAt: Date; // the timestamp when the file was uploaded
  projectId: ObjectId; // the ID of the project this file corresponds to
  filename: string; // the name of the file
  size: number; // the size of the file in bytes
  contentType: string; // the MIME type of the file
  type: string; // the internal datatype of the file (e.g., text, image)
  status: "annotated" | "unannotated";
}

interface TextMeta extends FileMeta {
  type: "text";
}

interface ImageMeta extends FileMeta {
  type: "image";
  width: number; // the width of the image in pixels
  height: number; // the height of the image in pixels
}
```

## Achitecture

Interaction with the database is divided into _managers_. This division modularizes our code and helps keep it organized.

### Strategy Pattern for Exports

One specified design pattern we used was the Strategy Pattern, which was used for exports. Essentially, we have an abstract base class, `_ExportStrategy` which specifies a private method (`_export`) for subclasses to override to provide functionality and a public wrapper method (`export`) that calles `_export` and handles some common operations done by all child strategies, such as fetching project details, initializing the ZIP file, and cleaning up created files in the case of an error.

To increase readability, some strategy implementation divide exports into more individual steps, but these steps are unique to each strategy. If a common pattern would arise, transitioning to a Template pattern would be better.

## File Structure

Most files within this directory implement a category of interaction with the database. See a description of each below.

- `__init__.py`: initializes this directory as an importable Python module. In terms of function, using `from DataAPI import db` automatically sets up all the managers located within this directory and provides a unified namespace to use them from. This is how a majority of our project interacts with the Database.

## Using this Module

The intended usage of this module is as follows:

```py
from DataAPI import db
```

This gives you access to the `db` namespace, which includes instantiated versions of all the managers.
