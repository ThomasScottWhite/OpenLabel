
from DataAPI.config import CONFIG

# note: if you want to modify config before initializing the app object, do so
#       before importing APP


if __name__ == "__main__":
    import subprocess

    subprocess.run([
        "uvicorn", "DataAPI.app:APP",
        "--host", "127.0.0.1",
        "--port", str(CONFIG.port),
        "--reload"
    ])

