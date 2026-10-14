"""Source-checkout entry point: python src [command] [options]."""
import argparse
import sys
from importlib import import_module

COMMANDS = {
    'serve': 'meeting_trace.web.server',
    'extract': 'meeting_trace.cli',
    'evaluate': 'meeting_trace.evaluation.runner',
    'test': 'meeting_trace.tools.test_runner',
    'package': 'meeting_trace.tools.package',
    'verify-probes': 'meeting_trace.tools.verify_probes',
    'revalidate': 'meeting_trace.evaluation.revalidate',
}


def main():
    parser = argparse.ArgumentParser(
        description='Meeting Trace source commands. Default: serve.',
        usage='python src [serve|extract|evaluate|test|package|verify-probes|revalidate] [options]')
    args = sys.argv[1:]
    if args and args[0] in ('-h', '--help'):
        parser.print_help()
        return 0
    if args and args[0] in COMMANDS:
        command, args = args[0], args[1:]
    elif not args or args[0].startswith('-'):
        command = 'serve'
    else:
        parser.error(f'Unknown command: {args[0]}')
    sys.argv = [f'{sys.argv[0]} {command}', *args]
    result = import_module(COMMANDS[command]).main()
    return result if isinstance(result, int) else 0


if __name__ == '__main__':
    sys.exit(main())
