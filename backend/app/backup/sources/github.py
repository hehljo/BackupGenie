"""
GitHub Backup Handler
Best Practice 02/2026: Uses --mirror clone for complete repository backup,
extends BackupHandler, retry with exponential backoff.
Supports discovery_mode 'all' (auto-discover via API) or 'manual' (explicit list).
"""
import subprocess
import logging
import os
import time
from app.backup.base import BackupHandler

logger = logging.getLogger(__name__)


class GitHubBackup(BackupHandler):
    """Handles GitHub repository backups using mirror clones"""

    def _resolve_repositories(self, token):
        """
        Resolve the list of repositories to back up based on discovery_mode.

        Returns:
            list: Repository full_name strings (e.g. 'user/repo')
        """
        discovery_mode = self.source_config.get('discovery_mode', 'manual')
        exclude = set(self.source_config.get('exclude', []))

        if discovery_mode == 'all':
            # Auto-discover all repos via GitHub API
            from app.services.github_discovery import discover_user_repos
            self.log("Discovery mode: all - fetching repos from GitHub API")
            try:
                repos = discover_user_repos(token)
                repo_names = [r['full_name'] for r in repos]

                # Apply exclude list
                if exclude:
                    self.log(f"Excluding {len(exclude)} repos: {', '.join(exclude)}")
                    repo_names = [r for r in repo_names if r not in exclude]

                self.log(f"Discovered {len(repo_names)} repos to back up")
                return repo_names
            except Exception as e:
                self.log(f"ERROR: Discovery failed: {e} - falling back to manual list")
                logger.error(f"GitHub discovery failed: {e}")
                return self.source_config.get('repositories', [])
        else:
            # Manual mode: use explicitly listed repos
            return self.source_config.get('repositories', [])

    def _get_token(self):
        """Get GitHub token from DB (global credential), then env var fallback"""
        from app.api.settings import get_credential
        token = get_credential('github_token')
        if token:
            return token
        # Legacy: token_env reference in source config
        credentials = self.source_config.get('credentials', {})
        token = os.environ.get(credentials.get('token_env', ''), '')
        return token

    def backup(self):
        """Execute GitHub backup"""
        token = self._get_token()

        if not token:
            raise Exception("GitHub token not configured. Set it in Settings → Credentials or as GITHUB_TOKEN env var.")

        repositories = self._resolve_repositories(token)
        files_synced = 0
        size_synced = 0
        options = self.source_config.get('options', {})

        for repo in repositories:
            try:
                self.log(f"Backing up repository: {repo}")

                # Parse repo (user/repo or org/repo)
                repo_dir = repo.replace('/', '_')
                repo_path = os.path.join(self.dest_path, f"{repo_dir}.git")

                # Build clone URL with token
                repo_url = f"https://{token}@github.com/{repo}.git"

                if os.path.exists(repo_path):
                    # Mirror exists, update all refs
                    self.log(f"Updating mirror for: {repo}")
                    result = self._run_with_retry(
                        ['git', '-C', repo_path, 'remote', 'update', '--prune'],
                        retries=3
                    )
                else:
                    # Create new mirror clone (captures all refs, tags, branches)
                    self.log(f"Creating mirror clone for: {repo}")
                    result = self._run_with_retry(
                        ['git', 'clone', '--mirror', repo_url, repo_path],
                        retries=3
                    )

                if result.stdout:
                    self.log(result.stdout)
                if result.stderr:
                    self.log(result.stderr)

                if result.returncode != 0:
                    self.log(f"WARNING: git command returned code {result.returncode}")

                # Get repository size
                repo_size = self._get_directory_size(repo_path)
                size_synced += repo_size
                files_synced += 1

                # Backup wiki if configured
                if options.get('include_wikis', False):
                    wiki_url = f"https://{token}@github.com/{repo}.wiki.git"
                    wiki_path = os.path.join(self.dest_path, f"{repo_dir}.wiki.git")
                    try:
                        if os.path.exists(wiki_path):
                            subprocess.run(
                                ['git', '-C', wiki_path, 'remote', 'update', '--prune'],
                                capture_output=True, text=True, timeout=120
                            )
                        else:
                            subprocess.run(
                                ['git', 'clone', '--mirror', wiki_url, wiki_path],
                                capture_output=True, text=True, timeout=120
                            )
                        self.log(f"Wiki backed up for {repo}")
                    except Exception:
                        self.log(f"No wiki found for {repo} (or access denied)")

                # Handle LFS if configured
                if options.get('include_lfs', False):
                    self.log(f"Fetching LFS objects for {repo}")
                    subprocess.run(
                        ['git', '-C', repo_path, 'lfs', 'fetch', '--all'],
                        capture_output=True, timeout=600
                    )

            except Exception as e:
                self.log(f"ERROR backing up {repo}: {str(e)}")
                logger.error(f"Error backing up {repo}: {e}")

        return {
            'files_synced': files_synced,
            'size_synced': size_synced,
            'logs': self.get_logs()
        }

    def _run_with_retry(self, cmd, retries=3, timeout=300):
        """Run command with exponential backoff retry"""
        last_result = None
        for attempt in range(retries):
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            if result.returncode == 0:
                return result
            last_result = result
            if attempt < retries - 1:
                wait_time = 2 ** attempt
                self.log(f"Retry {attempt + 1}/{retries} in {wait_time}s...")
                time.sleep(wait_time)
        return last_result
