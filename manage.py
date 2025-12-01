#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable? Did you forget to activate a virtual environment?"
        ) from exc
    # Convenience: if user runs `createsuperuser` before applying migrations,
    # run `migrate --noinput` automatically to avoid "no such table: users_user".
    if len(sys.argv) > 1 and sys.argv[1] == 'createsuperuser':
        try:
            execute_from_command_line([sys.argv[0], 'migrate', '--noinput'])
        except SystemExit:
            # If migrate exits (success or no changes), continue to createsuperuser
            pass
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
