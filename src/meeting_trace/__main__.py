"""Installed package entry point: python -m meeting_trace."""
from .web.server import main

if __name__ == '__main__':
    main()
