"""
GitHub Repository Discovery Service
Fetches all accessible repositories for the authenticated user,
including personal repos and organization repos with pagination.
"""
import logging
import requests

logger = logging.getLogger(__name__)

GITHUB_API_BASE = 'https://api.github.com'
PER_PAGE = 100
MAX_PAGES = 50  # Safety limit: max 5000 repos


def _get_headers(token):
    """Build GitHub API request headers"""
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }


def _paginate(url, headers, params=None):
    """Fetch all pages from a paginated GitHub API endpoint"""
    if params is None:
        params = {}
    params['per_page'] = PER_PAGE
    params['page'] = 1

    all_items = []
    while params['page'] <= MAX_PAGES:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        items = response.json()
        if not items:
            break

        all_items.extend(items)

        if len(items) < PER_PAGE:
            break
        params['page'] += 1

    return all_items


def _format_repo(repo):
    """Extract relevant fields from a GitHub API repo object"""
    return {
        'full_name': repo['full_name'],
        'private': repo['private'],
        'description': repo.get('description') or '',
        'size': repo.get('size', 0),
        'updated_at': repo.get('updated_at', ''),
        'fork': repo.get('fork', False),
        'archived': repo.get('archived', False),
        'has_wiki': repo.get('has_wiki', False),
        'default_branch': repo.get('default_branch', 'main'),
        'owner': repo.get('owner', {}).get('login', ''),
    }


def discover_user_repos(token):
    """
    Discover all repositories accessible to the authenticated user.
    Includes personal repos, collaborator repos, and org repos.

    Args:
        token: GitHub personal access token

    Returns:
        list: Repository metadata dicts

    Raises:
        requests.HTTPError: On API errors
    """
    headers = _get_headers(token)

    # GET /user/repos returns all repos the user has access to
    # (owned, collaborator, org member)
    repos = _paginate(
        f'{GITHUB_API_BASE}/user/repos',
        headers,
        params={'sort': 'updated', 'direction': 'desc'}
    )

    return [_format_repo(r) for r in repos]


def discover_all(token):
    """
    Discover all repos (user + orgs) and return a deduplicated list.

    Args:
        token: GitHub personal access token

    Returns:
        list: Deduplicated list of repo metadata dicts sorted by updated_at
    """
    headers = _get_headers(token)

    # /user/repos already includes org repos the user can access
    # Also fetch user info for response metadata
    resp = requests.get(f'{GITHUB_API_BASE}/user', headers=headers, timeout=15)
    resp.raise_for_status()
    user_info = resp.json()

    repos = discover_user_repos(token)

    # Deduplicate by full_name
    seen = set()
    unique_repos = []
    for repo in repos:
        if repo['full_name'] not in seen:
            seen.add(repo['full_name'])
            unique_repos.append(repo)

    # Sort by updated_at descending
    unique_repos.sort(key=lambda r: r['updated_at'], reverse=True)

    return {
        'user': user_info.get('login', ''),
        'repos': unique_repos,
        'total': len(unique_repos)
    }
