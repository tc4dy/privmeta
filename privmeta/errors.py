class PrivMetaError(Exception):
    pass


class UnsupportedFormat(PrivMetaError):
    pass


class MissingDependency(PrivMetaError):
    pass


class ValidationFailed(PrivMetaError):
    pass