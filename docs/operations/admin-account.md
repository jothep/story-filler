# Administrator accounts

Story content is managed in the Django admin at `/admin/` on the backend service. Django handles administrator authentication; there is no separate identity provider.

Keep usernames, passwords and connection strings out of this repository, issues and pull requests.

## Change your own password

Sign in to the admin and choose **Change password**, which opens `/admin/password_change/`.

## Reset a password or create an administrator

Use this when no administrator can sign in. The commands write directly to the production database.

1. In `backend/`, install the backend's Python dependencies as described in the [backend README](../../backend/README.md).
2. In the same shell, set `DATABASE_URL` (the Neon connection string), `SECRET_KEY` and `DEBUG=False`, which the settings module requires. Take the values from where you keep them privately, not from files in this repository, and keep them out of shell history. Values set in the shell take precedence over a local `backend/.env`.
3. Run one of:

   ```bash
   python manage.py changepassword <username>
   python manage.py createsuperuser
   ```

   `python change_admin_password.py <username>` does the same as `changepassword`; it asks for the new password twice and makes no change if the entries differ.

4. Close the shell, or unset the three variables, when you are done.

For a local development database, see the [local platform lab](../local-platform-lab.md), which runs `createsuperuser` inside the development containers.
