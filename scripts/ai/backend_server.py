"""Serve one candidate Django WSGI app on a parent-owned loopback socket.

This process exists only for the exact runner's strict conformance gate.
"""

import argparse
import os
import socket
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer


class TokenApplication:
    """Attach a per-run identity header to responses from the candidate app."""

    def __init__(self, application, token: str):
        """Hold the Django WSGI callable and run-owned response token.

        Args: application is the Django WSGI callable; token is random hex.
        Returns: None.
        Raises: None for reviewed inputs.
        Side effects: Stores in-process references only; no DB/network writes.
        """
        self.application = application
        self.token = token

    def __call__(self, environ, start_response):
        """Forward one WSGI request with the identity response header.

        Args: environ is WSGI request metadata; start_response sends headers.
        Returns: Iterable response body from the Django application.
        Raises: Application exceptions propagate to the WSGI server.
        Side effects: May read the run-owned DB through Django request handling.
        """
        def identified_start(status, headers, exc_info=None):
            """Add the run token to WSGI response headers.

            Args: status is HTTP status; headers are response header pairs;
                exc_info is optional WSGI error state.
            Returns: WSGI write callable from start_response.
            Raises: Errors from the caller-supplied start_response propagate.
            Side effects: Emits response headers only; no DB or file writes.
            """
            return start_response(status, [*headers, ("X-AI-Fixture-Token", self.token)], exc_info)

        return self.application(environ, identified_start)


def serve(fd: int, token: str) -> None:
    """Serve Django WSGI using exactly the inherited bound socket descriptor.

    Args: fd is a parent-bound IPv4 loopback socket; token is per-run hex.
    Returns: None after shutdown; normally serves until SIGTERM.
    Raises: OSError/ImportError/Django errors for invalid server setup.
    Side effects: Serves candidate requests and may read/write only the
        parent-provided ephemeral DB through Django settings.
    Business rule: Never binds a newly discovered port or reads DATABASE_URL
        from project env files; the wrapper supplies an isolated child env.
    """
    from django.core.wsgi import get_wsgi_application

    inherited = socket.socket(fileno=fd)
    host, port = inherited.getsockname()
    if host != "127.0.0.1" or port == 0 or inherited.family != socket.AF_INET:
        raise ValueError("Inherited socket is not bound to loopback")
    server = WSGIServer((host, port), WSGIRequestHandler, bind_and_activate=False)
    server.socket.close()
    server.socket = inherited
    server.server_address = (host, port)
    server.server_name = host
    server.server_port = port
    server.setup_environ()
    server.server_activate()
    server.set_app(TokenApplication(get_wsgi_application(), token))
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()


def main() -> int:
    """Parse the inherited FD and run token for one ephemeral WSGI server.

    Args: CLI --fd is a positive socket descriptor; token comes from the
        wrapper's child-only AI_FIXTURE_TOKEN environment variable.
    Returns: Zero after orderly shutdown.
    Raises: argparse/ValueError/OSError/Django errors for invalid setup.
    Side effects: Delegates to serve; no production DB or deployment state.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fd", required=True, type=int)
    args = parser.parse_args()
    token = os.environ["AI_FIXTURE_TOKEN"]
    if args.fd < 0 or len(token) != 32 or any(char not in "0123456789abcdef" for char in token):
        raise ValueError("Invalid server identity")
    serve(args.fd, token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
