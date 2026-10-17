"""Closed errors for the isolated synthetic-document UI boundary."""


class SyntheticDocumentError(ValueError):
    """Base class; messages are diagnostic-only and must not be rendered."""


class SyntheticDocumentNotFound(SyntheticDocumentError):
    pass


class SyntheticDocumentContentMissing(SyntheticDocumentError):
    pass


class SyntheticDocumentFormatUnsupported(SyntheticDocumentError):
    pass


class SyntheticDocumentDigestMismatch(SyntheticDocumentError):
    pass


class SyntheticDocumentFixtureInvalid(SyntheticDocumentError):
    pass
