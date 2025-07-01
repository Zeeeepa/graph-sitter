const express = require('express');
const axios = require('axios');
const router = express.Router();

// GitHub OAuth credentials
const GITHUB_CLIENT_ID = process.env.GITHUB_CLIENT_ID;
const GITHUB_CLIENT_SECRET = process.env.GITHUB_CLIENT_SECRET;
const GITHUB_REDIRECT_URI = process.env.GITHUB_REDIRECT_URI || 'http://localhost:3000/github/callback';

/**
 * Exchange GitHub OAuth code for access token
 * POST /api/github/callback
 */
router.post('/callback', async (req, res) => {
  try {
    const { code } = req.body;
    
    if (!code) {
      return res.status(400).json({ 
        success: false, 
        message: 'Authorization code is required' 
      });
    }
    
    // Exchange code for access token
    const tokenResponse = await axios.post(
      'https://github.com/login/oauth/access_token',
      {
        client_id: GITHUB_CLIENT_ID,
        client_secret: GITHUB_CLIENT_SECRET,
        code,
        redirect_uri: GITHUB_REDIRECT_URI,
      },
      {
        headers: {
          Accept: 'application/json',
        },
      }
    );
    
    const { access_token, token_type, scope } = tokenResponse.data;
    
    if (!access_token) {
      return res.status(400).json({ 
        success: false, 
        message: 'Failed to obtain access token' 
      });
    }
    
    // Get user information
    const userResponse = await axios.get('https://api.github.com/user', {
      headers: {
        Authorization: `token ${access_token}`,
      },
    });
    
    return res.json({
      success: true,
      message: 'GitHub authentication successful',
      data: {
        token: access_token,
        token_type,
        scope,
        user: userResponse.data,
      },
    });
  } catch (error) {
    console.error('GitHub callback error:', error);
    return res.status(500).json({
      success: false,
      message: 'Error processing GitHub authentication',
      error: error.message,
    });
  }
});

/**
 * Get repositories for the authenticated user
 * GET /api/github/repositories
 */
router.get('/repositories', async (req, res) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
      return res.status(401).json({ 
        success: false, 
        message: 'GitHub token is required' 
      });
    }
    
    const response = await axios.get('https://api.github.com/user/repos', {
      headers: {
        Authorization: `token ${token}`,
      },
      params: {
        sort: 'updated',
        per_page: 100,
      },
    });
    
    return res.json({
      success: true,
      message: 'Repositories retrieved successfully',
      data: {
        repositories: response.data,
      },
    });
  } catch (error) {
    console.error('Error fetching GitHub repositories:', error);
    return res.status(500).json({
      success: false,
      message: 'Error fetching GitHub repositories',
      error: error.message,
    });
  }
});

/**
 * Get user information
 * GET /api/github/user
 */
router.get('/user', async (req, res) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
      return res.status(401).json({ 
        success: false, 
        message: 'GitHub token is required' 
      });
    }
    
    const response = await axios.get('https://api.github.com/user', {
      headers: {
        Authorization: `token ${token}`,
      },
    });
    
    return res.json({
      success: true,
      message: 'User information retrieved successfully',
      data: {
        user: response.data,
      },
    });
  } catch (error) {
    console.error('Error fetching GitHub user:', error);
    return res.status(500).json({
      success: false,
      message: 'Error fetching GitHub user information',
      error: error.message,
    });
  }
});

module.exports = router;

