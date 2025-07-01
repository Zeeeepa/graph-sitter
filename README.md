# Deployment Validation System

A standalone application for managing deployment validations across GitHub repositories.

## Features

- GitHub OAuth integration
- Repository selection and pinning
- Deployment validation workflows
- Sandbox environments
- Secure secrets management
- Custom validation rules

## Setup

1. Create a GitHub OAuth App:
   - Go to GitHub Developer Settings
   - Create a new OAuth App
   - Set callback URL to `http://localhost:8000/api/v1/auth/github/callback`
   - Save the client ID and secret

2. Create `.env` file:
   ```env
   # GitHub OAuth
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   GITHUB_CALLBACK_URL=http://localhost:8000/api/v1/auth/github/callback

   # Security
   SECRET_KEY=your_secret_key
   ENCRYPTION_KEY=your_encryption_key

   # Database
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/validator
   ```

3. Start the application:
   ```bash
   docker-compose up -d
   ```

4. Access the application:
   - API: http://localhost:8000/api/docs
   - Frontend: http://localhost:3000

## Usage

1. Log in with GitHub:
   - Click "Login with GitHub"
   - Authorize the application

2. Select repositories:
   - View your repositories
   - Pin repositories you want to monitor

3. Configure validation workflows:
   - Create workflow with setup commands
   - Add environment variables and secrets
   - Define validation rules

4. Monitor validations:
   - View workflow history
   - Access sandbox environments
   - Check validation results

## API Documentation

Full API documentation is available at `/api/docs` when the application is running.

Key endpoints:

- `/api/v1/auth/*` - Authentication endpoints
- `/api/v1/repos/*` - Repository management
- `/api/v1/validation/*` - Validation workflows

## Development

1. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Run migrations:
   ```bash
   alembic upgrade head
   ```

3. Start development server:
   ```bash
   uvicorn src.app.main:app --reload
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

