#!/usr/bin/env python
"""
Change Django admin password remotely
Usage: python change_admin_password.py <username> <new_password>
"""
import os
import sys
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
    if len(sys.argv) != 3:
        print("Usage: python change_admin_password.py <username> <new_password>")
        print("\nAvailable users:")
        User = get_user_model()
        for user in User.objects.filter(is_superuser=True):
            print(f"  - {user.username} (superuser)")
        sys.exit(1)

    username = sys.argv[1]
    new_password = sys.argv[2]
    change_password(username, new_password)
