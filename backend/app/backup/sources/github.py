"""
GitHub Backup Handler
"""
import subprocess
import logging
import os
import shutil

logger = logging.getLogger(__name__)


class GitHubBackup:
    """Handles GitHub repository backups"""

    def __init__(self, source_config, dest_path):
        self.source_config = source_config
        self.dest_path = dest_path

    def backup(self):
        """Execute GitHub backup"""
        logs = []
        repositories = self.source_config.get('repositories', [])
        credentials = self.source_config.get('credentials', {})
        token = os.environ.get(credentials.get('token_env', ''), '')

        if not token:
            raise Exception("GitHub token not found in environment")

        files_synced = 0
        size_synced = 0

        for repo in repositories:
            try:
                logs.append(f"Backing up repository: {repo}")

                # Parse repo (user/repo or org/repo)
                repo_path = os.path.join(self.dest_path, repo.replace('/', '_'))

                # Build clone/pull URL with token
                repo_url = f"https://{token}@github.com/{repo}.git"

                if os.path.exists(repo_path):
                    # Repository exists, pull updates
                    logs.append(f"Updating existing repository: {repo}")
                    result = subprocess.run(
                        ['git', '-C', repo_path, 'pull'],
                        capture_output=True,
                        text=True
                    )
                else:
                    # Clone new repository
                    logs.append(f"Cloning new repository: {repo}")
                    result = subprocess.run(
                        ['git', 'clone', repo_url, repo_path],
                        capture_output=True,
                        text=True
                    )

                logs.append(result.stdout)
                if result.stderr:
                    logs.append(result.stderr)

                # Get repository size
                repo_size = self._get_directory_size(repo_path)
                size_synced += repo_size
                files_synced += 1

                # Handle LFS if configured
                options = self.source_config.get('options', {})
                if options.get('include_lfs', False):
                    logs.append(f"Fetching LFS objects for {repo}")
                    subprocess.run(
                        ['git', '-C', repo_path, 'lfs', 'fetch', '--all'],
                        capture_output=True
                    )

            except Exception as e:
                logs.append(f"ERROR backing up {repo}: {str(e)}")
                logger.error(f"Error backing up {repo}: {e}")

        return {
            'files_synced': files_synced,
            'size_synced': size_synced,
            'logs': '\n'.join(logs)
        }

    def _get_directory_size(self, path):
        """Get total size of directory"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        return total_size
