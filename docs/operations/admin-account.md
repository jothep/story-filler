# Administrator accounts

Story content is managed in the Django admin at `/admin/` on the backend service. Django handles administrator authentication; there is no separate identity provider.

Keep usernames, passwords and connection strings out of this repository, issues and pull requests.

## Change your own password

Sign in to the admin and choose **Change password**, which opens `/admin/password_change/`.

## Reset a password or create an administrator

Use this when no administrator can sign in. The commands write directly to the production database.

1. Open a [production database shell](production-shell.md) and check that it targets the service's database.
2. Run one of:

   ```bash
   python manage.py changepassword <username>
   python manage.py createsuperuser
   ```

   Both commands check the new password against Django's password validators.

3. Close the shell when you are done.

For a local development database, see the [local platform lab](../local-platform-lab.md), which runs `createsuperuser` inside the development containers.
