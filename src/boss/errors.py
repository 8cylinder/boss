class DependencyError(Exception):
    """Raised when a required dependency is not met."""


class PlatformError(Exception):
    """Raised when the platform is not supported."""


class SecurityError(Exception):
    """Raised when a security-related issue is encountered."""


class CommandError(Exception):
    """Raised when a command fails to execute properly."""


class ModuleRequestError(Exception):
    """Raised when the cli wanted module has more than one match."""
