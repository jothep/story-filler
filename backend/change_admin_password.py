#!/usr/bin/env python
"""
Change Django admin password remotely
Usage: python change_admin_password.py <username>
"""
import os
import sys
from getpass import getpass
import django

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maori_story_project.settings')
django.setup()

from django.contrib.auth import get_user_model

def change_password(username, new_password):
    User = get_user_model()
    try:
        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()
        print(f"✅ Password changed successfully for user: {username}")
        return True
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python change_admin_password.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    new_password = getpass('New password: ')
    if not new_password or new_password != getpass('Confirm password: '):
        sys.exit('Passwords must be nonempty and match; no changes made.')
    sys.exit(0 if change_password(username, new_password) else 1)
