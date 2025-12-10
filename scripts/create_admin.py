#!/usr/bin/env python3
"""
Create admin user script

Usage:
    python scripts/create_admin.py

Or with custom values:
    python scripts/create_admin.py --username admin --email admin@example.com --role admin
"""

import sys
import argparse
from getpass import getpass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.admin_user_repo import AdminUserRepository
from apps.api.auth.jwt import get_password_hash


def create_admin_user(username: str, email: str, password: str, role: str = "admin", full_name: str | None = None):
    """
    Create a new admin user

    Args:
        username: Username (must be unique)
        email: Email address (must be unique)
        password: Plain text password (will be hashed)
        role: User role (admin/editor/readonly)
        full_name: Full name (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    # Validate role
    valid_roles = ["admin", "editor", "readonly"]
    if role not in valid_roles:
        print(f"❌ Error: Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}")
        return False

    # Hash password
    password_hash = get_password_hash(password)

    # Create user
    with get_db_session() as session:
        repo = AdminUserRepository(session)

        # Check if username already exists
        existing_user = repo.get_by_username(username)
        if existing_user:
            print(f"❌ Error: Username '{username}' already exists")
            return False

        # Check if email already exists
        existing_email = repo.get_by_email(email)
        if existing_email:
            print(f"❌ Error: Email '{email}' already exists")
            return False

        # Create user
        try:
            user = repo.create_admin_user(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                full_name=full_name,
                is_active=True
            )
            session.commit()

            print(f"✅ Admin user created successfully!")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Role: {user.role}")
            print(f"   Full Name: {user.full_name or 'N/A'}")
            print(f"   User ID: {user.id}")

            return True

        except Exception as e:
            print(f"❌ Error creating user: {e}")
            session.rollback()
            return False


def interactive_create():
    """Interactive mode to create admin user"""
    print("=" * 60)
    print("Create Admin User - Interactive Mode")
    print("=" * 60)
    print()

    # Get username
    while True:
        username = input("Username (3-50 characters): ").strip()
        if len(username) < 3 or len(username) > 50:
            print("❌ Username must be 3-50 characters")
            continue
        break

    # Get email
    while True:
        email = input("Email: ").strip()
        if '@' not in email:
            print("❌ Invalid email format")
            continue
        break

    # Get password
    while True:
        password = getpass("Password (min 6 characters): ")
        if len(password) < 6:
            print("❌ Password must be at least 6 characters")
            continue

        password_confirm = getpass("Confirm password: ")
        if password != password_confirm:
            print("❌ Passwords do not match")
            continue
        break

    # Get role
    print("\nAvailable roles:")
    print("  1. admin     - Full system access")
    print("  2. editor    - Can create/update content")
    print("  3. readonly  - Read-only access")

    while True:
        role_choice = input("Select role (1-3, default: 1): ").strip() or "1"
        role_map = {"1": "admin", "2": "editor", "3": "readonly"}
        if role_choice in role_map:
            role = role_map[role_choice]
            break
        print("❌ Invalid choice")

    # Get full name (optional)
    full_name = input("Full name (optional): ").strip() or None

    print()
    print("=" * 60)
    print("Creating admin user with the following details:")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Role: {role}")
    print(f"  Full Name: {full_name or 'N/A'}")
    print("=" * 60)

    confirm = input("\nProceed? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return False

    return create_admin_user(username, email, password, role, full_name)


def main():
    parser = argparse.ArgumentParser(description="Create admin user for fishing agent")
    parser.add_argument("--username", help="Username")
    parser.add_argument("--email", help="Email address")
    parser.add_argument("--password", help="Password (WARNING: visible in process list)")
    parser.add_argument("--role", choices=["admin", "editor", "readonly"], default="admin", help="User role")
    parser.add_argument("--full-name", help="Full name")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    # Interactive mode
    if args.interactive or not (args.username and args.email):
        success = interactive_create()
        sys.exit(0 if success else 1)

    # Command line mode
    if not args.password:
        password = getpass("Password: ")
    else:
        password = args.password
        print("⚠️  WARNING: Password provided via command line is visible in process list")

    success = create_admin_user(
        username=args.username,
        email=args.email,
        password=password,
        role=args.role,
        full_name=args.full_name
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
