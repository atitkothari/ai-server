"""Custom Error modules used across the codebase."""


class BaseCustomError(BaseException):
    """Base class to create custom error objects."""

    def __init__(self, message: str, error_code: str) -> None:
        super().__init__(message)
        self.error_code = error_code

    def __str__(self) -> str:
        return f"{self.error_code}:: {super().__str__()}"


class InternalServerError(Exception):
    """Indicates cases when the server side code breaks."""


class ModelResponseError(BaseCustomError):
    """Indicates cases when model response is either invalid or failed."""


class ModelResponseParseError(BaseCustomError):
    """Indicates cases when model responses is/are unparsable."""


class NotImplementedError(BaseCustomError):
    """Indicates that the given functionality is yet to be implemented."""


class IncompletePromptDictionaryError(BaseCustomError):
    """Indicates that the passed prompt dict didn't have sufficient keys."""


class ModelInitializationFailedError(BaseCustomError):
    """Indicates issues in initialization of model APIs."""


class InvalidCharacterIdError(BaseCustomError):
    """Indicates issues in generating character id for a character profile."""


class InvalidCharacterProfileError(BaseCustomError):
    """Indicates issues in creating a valid Character Profile."""


class IncompleteModelResponseError(BaseCustomError):
    """Indicates that the model response is missing parts."""


class InvalidFrameBreakdownError(BaseCustomError):
    """Indicates issues in creating a valid Frame breakdown."""


class InvalidVisualStyleSelectionError(BaseCustomError):
    """Indicates invalid Visual Style was passed."""


class UnknownErrorOccured(BaseCustomError):
    """Unknown code failure."""


class InvalidConfigError(BaseCustomError):
    """Indicates invalid config for inpaint or reference image generation."""


class HTTPException(BaseCustomError):
    """Indicates that an HTTP request failed due to an incorrect URL."""


class UnsupportedFileFormat(BaseCustomError):
    """Unsupported file format, only .txt, .pdf and .fountain are supported"""
