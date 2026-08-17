class ApplicationError(Exception):
    status_code = 500

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(ApplicationError):
    status_code = 400


class AuthenticationError(ApplicationError):
    status_code = 401


class AuthorizationError(ApplicationError):
    status_code = 403


class NotFoundError(ApplicationError):
    status_code = 404


class ConflictError(ApplicationError):
    status_code = 409
