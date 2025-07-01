# GitHub OAuth Integration

This project implements GitHub OAuth authentication instead of using GitHub Personal Access Tokens (PATs).

## Setup Instructions

### 1. Create a GitHub OAuth App

1. Go to your GitHub account settings
2. Navigate to "Developer settings" > "OAuth Apps" > "New OAuth App"
3. Fill in the required information:
   - Application name: Your app name
   - Homepage URL: Your app's homepage (e.g., `http://localhost:3000`)
   - Authorization callback URL: Your callback URL (e.g., `http://localhost:3000/github/callback`)
4. Click "Register application"
5. Note your Client ID and generate a Client Secret

### 2. Configure Environment Variables

#### Backend (.env file in backend directory)

```
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:3000/github/callback
PORT=5000
NODE_ENV=development
```

#### Frontend (.env file in frontend directory)

```
REACT_APP_GITHUB_CLIENT_ID=your_github_client_id
REACT_APP_GITHUB_REDIRECT_URI=http://localhost:3000/github/callback
REACT_APP_API_URL=http://localhost:5000/api
```

### 3. Install Dependencies and Run

#### Backend

```bash
cd src/contexten/backend
npm install
npm run dev
```

#### Frontend

```bash
cd src/contexten/frontend
npm install
npm start
```

## How It Works

1. User clicks "Login with GitHub" button
2. User is redirected to GitHub for authorization
3. After authorization, GitHub redirects back to our app with a code
4. Our backend exchanges the code for an access token
5. The access token is stored in localStorage and used for GitHub API requests
6. User information is displayed in the UI

## API Endpoints

- `POST /api/github/callback`: Exchange code for token
- `GET /api/github/repositories`: Get user repositories
- `GET /api/github/user`: Get user information

## Security Considerations

- The GitHub OAuth flow is more secure than using PATs
- The token exchange happens on the backend to protect the client secret
- Tokens are stored in localStorage and should be handled securely
- Consider implementing token refresh and expiration handling for production use

