# Production Database Setup Guide

## Overview
This guide ensures your MT5 Dashboard database is correctly configured for production use.

## Fixed Issues
1. ✅ Fixed `ModuleNotFoundError: No module named 'backend.database.base'`
   - Changed import from `backend.database.base import init_db` to `backend.database import init_database`
   - Updated function call from `init_db()` to `init_database()`

## Database Configuration

### 1. Environment Variables
Create a `.env` file in the root directory with the following:

```bash
# Database Configuration
DATABASE_PATH=data/mt5_dashboard.db  # For SQLite
# For PostgreSQL (recommended for production):
# DATABASE_URL=postgresql://user:password@host:5432/dbname

# Server Configuration
ENVIRONMENT=production
MT5_API_PORT=8000
MT5_WS_PORT=8765

# Security
MT5_AUTH_TOKEN=your_secure_token_here

# Logging
LOG_LEVEL=INFO
```

### 2. Database Initialization
Initialize the database with proper schema:

```bash
cd backend
python -m database.init_db
```

### 3. Apply Migrations
Ensure all migrations are applied:

```bash
cd backend
python -c "from database.migrations import apply_migrations; apply_migrations()"
```

### 4. Verify Database Integrity
Check database health:

```bash
cd backend
python -c "from database.init_db import verify_database_integrity; print('Database OK' if verify_database_integrity() else 'Database Issues Found')"
```

## Frontend Configuration

### 1. Environment Setup
The frontend `.env` file has been created with proper API endpoints:

```bash
# Frontend .env
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_WS_URL=ws://127.0.0.1:8765
```

For production, update these to your actual domain:
```bash
REACT_APP_API_URL=https://your-api-domain.com
REACT_APP_WS_URL=wss://your-websocket-domain.com
```

### 2. Build for Production
```bash
cd frontend
npm install
npm run build
```

## Production Checklist

### Database
- [x] Database module imports fixed
- [x] Error handling implemented with proper logging
- [x] Migration system in place
- [x] Connection pooling configured (SQLite: StaticPool)
- [ ] Backup strategy implemented
- [ ] Connection limits configured
- [ ] Query optimization reviewed

### Security
- [ ] Change default auth token
- [ ] Enable HTTPS/WSS in production
- [ ] Configure CORS properly
- [ ] Implement rate limiting
- [ ] Add input validation
- [ ] Enable SQL injection protection (SQLAlchemy provides this)

### Performance
- [ ] Consider PostgreSQL/MySQL for production (SQLite is file-based)
- [ ] Implement connection pooling for chosen database
- [ ] Add database indexes for frequently queried fields
- [ ] Configure caching where appropriate

### Monitoring
- [ ] Set up database monitoring
- [ ] Configure log aggregation
- [ ] Implement health checks
- [ ] Set up alerting for database issues

## Starting the System

### Development Mode
```bash
# Start backend
cd backend
python main.py

# Start frontend (in another terminal)
cd frontend
npm start
```

### Production Mode
```bash
# Using the start script
python start.py --production

# Or manually
cd backend
ENVIRONMENT=production python start_complete_server.py
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_PATH or DATABASE_URL environment variables
   - Ensure database file/server is accessible
   - Verify permissions on database directory

2. **Migration Failures**
   - Check migration files in `backend/database/migrations/`
   - Verify database permissions for schema modifications
   - Review migration logs for specific errors

3. **Frontend Connection Issues**
   - Verify REACT_APP_API_URL matches backend address
   - Check CORS configuration in backend
   - Ensure backend is running before starting frontend

## Next Steps

1. **Choose Production Database**
   - SQLite is suitable for small deployments
   - PostgreSQL recommended for production
   - MySQL/MariaDB also supported via SQLAlchemy

2. **Set Up Monitoring**
   - Implement database query logging
   - Set up performance monitoring
   - Configure error alerting

3. **Implement Backups**
   - Daily automated backups
   - Test restore procedures
   - Off-site backup storage

4. **Security Hardening**
   - Use environment-specific secrets
   - Enable SSL/TLS for all connections
   - Implement proper authentication

## Support

For additional help with database setup:
1. Check logs in `backend/logs/`
2. Run verification script: `python verify_setup.py`
3. Review `backend/database/README.md` for detailed documentation