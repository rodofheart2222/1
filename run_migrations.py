#!/usr/bin/env python3
"""
Simple script to run database migrations
"""

import sys
import os

# Add backend to the path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

try:
    from database.migrations import apply_migrations
    
    print("Applying database migrations...")
    success = apply_migrations()
    
    if success:
        print("✅ All migrations applied successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Migration error: {e}")
    sys.exit(1)


