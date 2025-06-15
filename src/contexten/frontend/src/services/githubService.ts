import { createAppAuth } from '@octokit/auth-app';
import { Octokit } from '@octokit/rest';
import type { FileChange } from '../types/github';

// GitHub App credentials
const GITHUB_APP_ID = process.env.REACT_APP_GITHUB_APP_ID;
const GITHUB_PRIVATE_KEY = process.env.REACT_APP_GITHUB_PRIVATE_KEY?.replace(/\\n/g, '\n');

// GitHub OAuth App credentials
const GITHUB_CLIENT_ID = process.env.REACT_APP_GITHUB_CLIENT_ID;
const GITHUB_REDIRECT_URI = process.env.REACT_APP_GITHUB_REDIRECT_URI || window.location.origin + '/github/callback';

/**
 * Creates an Octokit instance authenticated with GitHub App credentials
 */
const createOctokit = async (installationId: number) => {
  if (!GITHUB_APP_ID || !GITHUB_PRIVATE_KEY) {
    throw new Error('GitHub App credentials are not configured');
  }

  const octokit = new Octokit({
    authStrategy: createAppAuth,
    auth: {
      appId: GITHUB_APP_ID,
      privateKey: GITHUB_PRIVATE_KEY,
      installationId,
    },
  });

  return octokit;
};

/**
 * Initiates the GitHub OAuth flow
 */
export const initiateGitHubLogin = () => {
  if (!GITHUB_CLIENT_ID) {
    throw new Error('GitHub OAuth client ID is not configured');
  }

  const scope = 'repo user';
  const authUrl = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${encodeURIComponent(GITHUB_REDIRECT_URI)}&scope=${scope}`;
  
  // Open GitHub authorization page
  window.location.href = authUrl;
};

/**
 * Handles the GitHub OAuth callback
 * This should be called from your callback route component
 */
export const handleGitHubCallback = async (code: string): Promise<{ token: string; user: any }> => {
  // In a real app, you would exchange the code for a token via your backend
  // to avoid exposing your client secret in the frontend
  const response = await fetch('/api/github/callback', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ code }),
  });

  if (!response.ok) {
    throw new Error('Failed to exchange code for token');
  }

  const data = await response.json();
  
  // Store the token in localStorage
  localStorage.setItem('github_token', data.token);
  
  return data;
};

/**
 * Checks if the user is authenticated with GitHub
 */
export const isGitHubAuthenticated = (): boolean => {
  return !!localStorage.getItem('github_token');
};

/**
 * Gets the authenticated GitHub user
 */
export const getGitHubUser = async (): Promise<any> => {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });
  const { data } = await octokit.users.getAuthenticated();
  
  return data;
};

/**
 * Logs out from GitHub
 */
export const logoutFromGitHub = (): void => {
  localStorage.removeItem('github_token');
};

// Pull request related functions
export const getPullRequestDetails = async (
  owner: string,
  repo: string,
  pullNumber: number,
) => {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });
  const { data: pullRequest } = await octokit.pulls.get({
    owner,
    repo,
    pull_number: pullNumber,
  });

  return pullRequest;
};

export const getPullRequestFiles = async (
  owner: string,
  repo: string,
  pullNumber: number,
): Promise<FileChange[]> => {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });
  const { data: files } = await octokit.pulls.listFiles({
    owner,
    repo,
    pull_number: pullNumber,
    per_page: 100,
  });

  return files.map(
    (file: {
      filename: string
      status:
        | 'added'
        | 'removed'
        | 'modified'
        | 'renamed'
        | 'copied'
        | 'changed'
        | 'unchanged'
      additions: number
      deletions: number
      changes: number
      patch?: string | undefined
    }) => {
      const extension = file.filename.split('.').pop() || 'unknown';

      return {
        filename: file.filename,
        status: file.status,
        additions: file.additions,
        deletions: file.deletions,
        changes: file.changes,
        fileType: extension,
        patch: file.patch || '',
      };
    },
  );
};

export const createPullRequestComment = async (
  owner: string,
  repo: string,
  pullNumber: number,
  body: string,
) => {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });
  const response = await octokit.issues.createComment({
    owner,
    repo,
    issue_number: pullNumber,
    body,
  });

  return response.data;
};

export const updatePullRequestComment = async (
  owner: string,
  repo: string,
  commentId: number,
  body: string,
) => {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });
  const response = await octokit.issues.updateComment({
    owner,
    repo,
    comment_id: commentId,
    body,
  });

  return response.data;
};

/**
 * Gets comments from a GitHub issue or pull request
 * @returns Array of issue comments
 */
export const getIssueComments = async (
  owner: string,
  repo: string,
  issueNumber: number,
) => {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });
  const { data: comments } = await octokit.issues.listComments({
    owner,
    repo,
    issue_number: issueNumber,
    per_page: 100,
  });

  return comments;
};

export async function getRepositories() {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });
  const { data } = await octokit.repos.listForAuthenticatedUser({
    per_page: 100,
    sort: 'updated',
  });

  return data;
}

export const getRepository = async (owner: string, repo: string) => {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });
  const { data } = await octokit.repos.get({
    owner,
    repo,
  });

  return data;
};

/**
 * Gets file content and SHA from GitHub repository
 * @returns Object containing content and SHA
 */
export const getFileContent = async (
  owner: string,
  repo: string,
  filePath: string,
  ref: string,
): Promise<{ content: string | null; sha: string | null }> => {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });

  try {
    const { data } = await octokit.repos.getContent({
      owner,
      repo,
      path: filePath,
      ref,
    });

    if ('type' in data && data.type === 'file' && 'content' in data) {
      return {
        content: Buffer.from(data.content, 'base64').toString('utf-8'),
        sha: data.sha,
      };
    }

    console.warn('Not a file:', filePath);
    return { content: null, sha: null };
  } catch (error) {
    // Handle 404 errors silently as they're expected when files don't exist
    const isNotFoundError =
      (error instanceof Error && 'status' in error && error.status === 404) ||
      (error instanceof Error && error.message.includes('Not Found')) ||
      (typeof error === 'object' &&
        error !== null &&
        'status' in error &&
        error.status === 404);

    if (isNotFoundError) {
      console.info(
        `File not found: ${filePath} in ${owner}/${repo}@${ref}`,
      );
    } else {
      // Log other errors as they might indicate actual problems
      console.error(`Error fetching file content for ${filePath}:`, error);
    }
    return { content: null, sha: null };
  }
};

export const getRepositoryBranches = async (
  owner: string,
  repo: string,
) => {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });
  const branches = await octokit.paginate(octokit.repos.listBranches, {
    owner,
    repo,
    per_page: 100,
  });

  return branches;
};

/**
 * Creates or updates a file in the GitHub repository
 * @param sha If provided, updates an existing file. If not provided, creates a new file.
 * @returns Object containing success status and SHA of the created/updated file
 */
export const createOrUpdateFileContent = async (
  owner: string,
  repo: string,
  filePath: string,
  content: string,
  message: string,
  branch = 'main',
  sha?: string,
): Promise<{ success: boolean; sha: string | null }> => {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });

  try {
    const response = await octokit.repos.createOrUpdateFileContents({
      owner,
      repo,
      path: filePath,
      message,
      content: Buffer.from(content).toString('base64'),
      branch,
      ...(sha ? { sha } : {}),
    });

    return {
      success: true,
      sha: response.data.content?.sha || null,
    };
  } catch (error) {
    console.error(`Error creating/updating file ${filePath}:`, error);
    return { success: false, sha: null };
  }
};

/**
 * Gets the latest commit information for a repository
 * @returns Latest commit details or null
 */
export const getLastCommit = async (
  owner: string,
  repo: string,
  branch = 'main',
): Promise<{
  sha: string
  date: string
  message: string
  author: string
} | null> => {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });

  try {
    const { data: commits } = await octokit.repos.listCommits({
      owner,
      repo,
      sha: branch,
      per_page: 1, // Only need the latest commit
    });

    if (!commits || commits.length === 0) {
      return null;
    }

    const latestCommit = commits[0];
    if (!latestCommit || !latestCommit.commit) {
      return null;
    }

    return {
      sha: latestCommit.sha || '',
      date:
        latestCommit.commit.committer?.date ||
        latestCommit.commit.author?.date ||
        '',
      message: latestCommit.commit.message || '',
      author:
        latestCommit.commit.author?.name ||
        latestCommit.commit.committer?.name ||
        '',
    };
  } catch (error) {
    console.error(`Error fetching latest commit for ${owner}/${repo}:`, error);
    return null;
  }
};

/**
 * Gets organization information for a repository
 * @returns Organization avatar URL or null
 */
export const getOrganizationInfo = async (
  owner: string,
  repo: string,
): Promise<{ avatar_url: string } | null> => {
  const token = localStorage.getItem('github_token');
  
  if (!token) {
    throw new Error('Not authenticated with GitHub');
  }
  
  const octokit = new Octokit({ auth: token });

  try {
    const { data } = await octokit.repos.get({
      owner,
      repo,
    });

    return {
      avatar_url: data.organization?.avatar_url || '',
    };
  } catch (error) {
    console.error(
      `Error fetching organization info for ${owner}/${repo}:`,
      error,
    );
    return null;
  }
};

export default {
  initiateGitHubLogin,
  handleGitHubCallback,
  isGitHubAuthenticated,
  getGitHubUser,
  logoutFromGitHub,
  getPullRequestDetails,
  getPullRequestFiles,
  createPullRequestComment,
  updatePullRequestComment,
  getIssueComments,
  getRepositories,
  getRepository,
  getFileContent,
  getRepositoryBranches,
  createOrUpdateFileContent,
  getLastCommit,
  getOrganizationInfo,
};

