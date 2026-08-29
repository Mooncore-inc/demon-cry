from importlib.metadata import PackageNotFoundError, version

def get_version():
    try:
        _version = version("demon-cry")
    except PackageNotFoundError:
        _version = "0.0.0"
    return _version
