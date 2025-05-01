class UserAlreadyExists(Exception):
    pass


class ResourceNotFound(Exception):
    pass


class PermissionError(Exception):
    pass


class EmailAlreadyExists(Exception):
    pass


class RoleNotFound(Exception):
    pass


class InvalidPatchMap(Exception):
    pass


class ProjectNameExists(Exception):
    pass
