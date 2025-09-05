"""pipecat_macos_transport: Local macOS transport skeleton.

This package will provide:
- LocalMacTransportParams
- LocalMacTransport

The implementation will be migrated from your existing repos.
"""

__all__ = [
    "LocalMacTransportParams",
    "LocalMacTransport",
]

try:
    from .local_mac_transport import LocalMacTransportParams, LocalMacTransport  # noqa: F401
except Exception:
    # Allow import of the package before implementation lands
    pass

