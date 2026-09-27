"""Administrative commands.

Usage:
    python manage.py create-admin --email you@example.com --name "Your Name"
    python manage.py reset-password --email you@example.com
    python manage.py backup                  # write a backup now (also runs automatically every day)
    python manage.py list-backups
    python manage.py restore <archive>       # stop the API first; current data is kept for rollback

Passwords are generated and printed once; users are asked to change them after signing in.
"""

import argparse
import sys

from services.platform_store import get_platform_store
from services.security import hash_password, temporary_password


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-admin", help="Create an administrator account")
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    reset = sub.add_parser("reset-password", help="Generate a new temporary password for a user")
    reset.add_argument("--email", required=True)
    sub.add_parser("backup", help="Back up every database and uploaded file now")
    sub.add_parser("list-backups", help="List backups, newest first")
    restore = sub.add_parser("restore", help="Restore a backup (stop the API first)")
    restore.add_argument("archive")
    args = parser.parse_args()

    if args.command in ("backup", "list-backups", "restore"):
        from services import backup
        if args.command == "backup":
            print(f"Backup written: {backup.create_backup()}")
        elif args.command == "list-backups":
            print("\n".join(backup.list_backups()) or "No backups yet.")
        else:
            try:
                moved = backup.restore_backup(args.archive)
            except ValueError as e:
                sys.exit(str(e))
            print("Restored. Previous data kept at:\n" + "\n".join(f"  {p}" for p in moved.values()))
        return

    store = get_platform_store()
    password = temporary_password()
    if args.command == "create-admin":
        if store.get_user_by_email(args.email):
            sys.exit(f"A user with email {args.email} already exists (use reset-password).")
        store.create_user(args.email, args.name, hash_password(password), "admin", must_change_password=True)
        print(f"Administrator created: {args.email}")
    else:
        user = store.get_user_by_email(args.email)
        if not user:
            sys.exit(f"No user with email {args.email}.")
        store.update_user(user["id"], password_hash=hash_password(password), must_change_password=1)
        store.delete_user_sessions(user["id"])
        print(f"Password reset: {args.email}")
    print(f"Temporary password (shown once): {password}")


if __name__ == "__main__":
    main()
