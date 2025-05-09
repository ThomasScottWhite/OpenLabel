# OpenLabel

OpenLabel aims to be a flexible, open source, and free-to-use solution to AI annotations.

## Getting Started

To preserve data privacy, OpenLabel is designed to be hosted locally, allowing users to maintain full control over their data. OpenLabel also intends to be modular, allowing each component to be run on different machins, if desired.

- For info on how to run the app, see [Running the App](#running-the-app).
- For instruction on setting up a development environment, see [Environment Setup](#environment-setup).

## Project Directory

- Annotations/Data Backend: [OpenLabelBackend/DataAPI/README.md](./OpenLabelBackend/DataAPI/README.md)
  - Database: [OpenLabelBackend/DataAPI/db/README.md](./OpenLabelBackend/DataAPI/db/README.md)
- Model Training/Pre-Annotation Backend: [OpenLabelBackend/TrainingAPI/README.md](./OpenLabelBackend/DataAPI/README.md)
  - this feature has not yet been developed.
- Frontend/GUI: [OpenLabelFrontend/README.md](./OpenLabelFrontend/README.md)

## Contents

- [Getting Started](#getting-started)
- [Running the App](#running-the-app)
- [Environment Setup](#environment-setup)
  - [Install Conda](#install-conda)
  - [Install Podman](#install-podman)
  - [Environment Creation](#environment-creation)
- [Running the App Locally](#running-the-app-locally)
  - [Start the Database](#start-the-database)
  - [Start the Backend (API)](#start-the-backend-api)
  - [Start the Frontend (Web GUI)](#start-the-frontend-web-gui)

## Running the App

Currently, this aspect of OpenLabel is under construction! We use a container for database hosting, but currently do not have containers for the app itself. Instead, you may run the app locally by following [Environment Setup](#environment-setup), then [Running the App Locally](#running-the-app-locally).

## Environment Setup

### Install Conda

We used [Minforge](https://github.com/conda-forge/miniforge) as our environment manager, but any `conda` installation should work.

Install Miniforge: <https://github.com/conda-forge/miniforge/releases>

### Install Podman

We host our database in a Podman/Docker container, so you will need podman or docker. Podman is recommended as it is what was used when testing/creating the project. Here are instructions for installing podman: <https://podman.io/docs/installation>

Note: if you are using Docker instead, replace `podman` with `docker` in all future commands.

### Environment Creation

If you have `conda` installed (recommended):

```sh
git clone https://github.com/ThomasScottWhite/DatabaseProject.git
cd ./DatabaseProject
conda env create -f environment.yml -n openlabel
conda activate openlabel
cd ./OpenLabelFrontend
npm install
```

Now, your environment should be ready!

## Running the App Locally

The easiest way to run this code is using three terminal instances: one for the frontend, one for the backend, and one for the database. If you can't open multiple terminals (perhaps you are `ssh`'d into a machine), you can use a terminal multiplexer such as `tmux`.

### Start the Database

You need to have `podman` or `docker` installed to run the database. If you are using docker, replace `podman` with `docker`, and it should function the same.

```sh
podman run --detach --replace --name openlabel_db -p 27017:27017 docker.io/mongodb/mongodb-community-server:latest
```

**NOTE:** This command does not mount data to the drive, so all data is lost once the container is killed!

### Start the Backend (API)

In another terminal, with the project's `conda` environment activated (unless you are not using `conda`), run the following _from the `OpenLabel/OpenLabelBackend/` directory_:

```sh
python -m DataAPI
```

This will start the backend on `localhost:6969`. You can go to <http://localhost:6969/docs> while the backend is running to view auto-generated documentation for the backend.

### Start the Frontend (Web GUI)

In yet another terminal, with the project's `conda` environment activated (unless you are not using `conda`), run the following _from the `OpenLabel/OpenLabelFrontend/` directory_:

```sh
npm run dev
```

This will start the frontend on whatever port is printed to the console (likely <http://localhost:5173>).

## Future Development and Features

Some other features we plan to add to the app include:

- Role-based authentication of users
- Automatic model training and pre-annotation
