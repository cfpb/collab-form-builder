#!/usr/bin/env python
import os, os.path
import sys
sys.path.append(os.path.join(os.getcwd(), 'src'))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dev.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
