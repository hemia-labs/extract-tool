class ExtractionError(Exception):
    status_code = 500

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class UnsupportedFileTypeError(ExtractionError):
    status_code = 415


class FileTooLargeError(ExtractionError):
    status_code = 413


class PdfPageLimitExceededError(ExtractionError):
    status_code = 413


class ExtractionFailedError(ExtractionError):
    status_code = 422


class OcrFailedError(ExtractionError):
    status_code = 422
