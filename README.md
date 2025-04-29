# OpenLabel

## Environment Setup

### Install Conda

We used [Minforge](https://github.com/conda-forge/miniforge) as our environment manager, but any `conda` installation should work.

Install Miniforge: https://github.com/conda-forge/miniforge/releases

### Install Podman

We host our database in a Podman/Docker container, so you will need podman or docker. Podman is recommended as it is what was used when testing/creating the project. Here are instructions for installing podman: https://podman.io/docs/installation

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

TODO: include building database container in environment creation

Now, your environment should be ready!

## Running the Code

The easiest way to run this code is using three terminal instances: one for the frontend, one for the backend, and one for the database. If you can't open multiple terminals (perhaps you are `ssh`'d into a machine), you can use a terminal multiplexer such as `tmux`.

### Start the Database

You need to have `podman` or `docker` installed to run the database. If you are using docker, replace `podman` with `docker`, and it should function the same.

```sh
podman run --detach --name openlabel_db --replace -p 27017:27017 docker.io/mongodb/mongodb-community-server:latest
```

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
