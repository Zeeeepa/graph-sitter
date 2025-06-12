# Security Configuration Guide

## Required Secrets

This system requires the following secrets to be configured in your GitHub repository:

1. `GITHUB_TOKEN` (automatically provided by GitHub Actions)
2. `CODEGEN_ORG_ID` (your Codegen organization ID)
3. `CODEGEN_API_TOKEN` (your Codegen API token)

## Setting Up Secrets

1. Go to your repository's Settings
2. Navigate to Secrets and Variables > Actions
3. Click "New repository secret"
4. Add each required secret:
   - Name: `CODEGEN_ORG_ID`
   - Value: Your Codegen organization ID
   
   - Name: `CODEGEN_API_TOKEN`
   - Value: Your Codegen API token

## Security Best Practices

1. Never commit secrets or credentials to the repository
2. Regularly rotate your API tokens
3. Use environment variables for local development
4. Monitor GitHub's security alerts
5. Review access to repository secrets

## Local Development

Create a `.env` file (do not commit this file):

```bash
CODEGEN_ORG_ID=your-org-id
CODEGEN_API_TOKEN=your-api-token
```

Then source it:

```bash
source .env
```

## Credential Rotation

1. Generate new API tokens in Codegen dashboard
2. Update GitHub repository secrets
3. Update local .env files
4. Revoke old tokens

## Security Checks

The system automatically:
1. Validates required secrets
2. Checks for security issues in PRs
3. Analyzes code for potential vulnerabilities
4. Reports findings in PR comments

## Reporting Security Issues

If you discover a security issue:
1. Do not open a public issue
2. Email security@your-domain.com
3. Include detailed information about the vulnerability
4. Wait for confirmation before disclosing publicly

