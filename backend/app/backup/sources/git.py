"""
Generic Git Repository Backup Handler
Supports: GitLab, Gitea, Forgejo, Bitbucket, Codeberg, and other Git platforms
"""
import subprocess
import logging
import os
from app.backup.base import BackupHandler

logger = logging.getLogger(__name__)


class GitBackup(BackupHandler):
    """Handles Git repository backups from various platforms"""

    # Platform-specific URL templates
    PLATFORMS = {
        'gitlab': 'https://oauth2:{token}@gitlab.com/{repo}.git',
        'gitlab-selfhosted': 'https://oauth2:{token}@{host}/{repo}.git',
        'gitea': 'https://{token}@{host}/{repo}.git',
        'forgejo': 'https://{token}@{host}/{repo}.git',
        'bitbucket': 'https://x-token-auth:{token}@bitbucket.org/{repo}.git',
        'codeberg': 'https://{token}@codeberg.org/{repo}.git',
    }

    def backup(self):
        """Execute Git repository backup"""
        repositories = self.source_config.get('repositories', [])
        credentials = self.source_config.get('credentials', {})
        platform = self.source_config.get('platform', 'gitlab')
        host = self.source_config.get('host', '')  # For self-hosted instances

        # Get token from environment
        token_env = credentials.get('token_env', '')
        token = self._get_env_credential(token_env) if token_env else ''

        if not token and platform not in ['gitlab', 'gitea', 'forgejo', 'bitbucket', 'codeberg']:
            raise Exception(f"Authentication token required for {platform}")

        files_synced = 0
        size_synced = 0

        for repo in repositories:
            try:
                self.log(f"Backing up repository: {repo}")

                # Parse repo (user/repo or org/repo)
                repo_path = os.path.join(self.dest_path, repo.replace('/', '_'))

                # Build clone/pull URL with token
                repo_url = self._build_repo_url(platform, repo, token, host)

                if os.path.exists(repo_path):
                    # Repository exists, pull updates
                    self.log(f"Updating existing repository: {repo}")
                    result = subprocess.run(
                        ['git', '-C', repo_path, 'pull'],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                else:
                    # Clone new repository
                    self.log(f"Cloning new repository: {repo}")
                    result = subprocess.run(
                        ['git', 'clone', repo_url, repo_path],
                        capture_output=True,
                        text=True,
                        timeout=600
                    )

                if result.stdout:
                    self.log(result.stdout)
                if result.stderr and 'warning' not in result.stderr.lower():
                    self.log(result.stderr)

                # Get repository size
                repo_size = self._get_directory_size(repo_path)
                size_synced += repo_size
                files_synced += 1

                # Handle LFS if configured
                options = self.source_config.get('options', {})
                if options.get('include_lfs', False):
                    self.log(f"Fetching LFS objects for {repo}")
                    subprocess.run(
                        ['git', '-C', repo_path, 'lfs', 'fetch', '--all'],
                        capture_output=True,
                        timeout=300
                    )

                # Backup wiki if configured and exists
                if options.get('include_wikis', False):
                    wiki_url = repo_url.replace('.git', '.wiki.git')
                    wiki_path = repo_path + '_wiki'

                    try:
                        if os.path.exists(wiki_path):
                            subprocess.run(
                                ['git', '-C', wiki_path, 'pull'],
                                capture_output=True,
                                text=True,
                                timeout=300
                            )
                        else:
                            subprocess.run(
                                ['git', 'clone', wiki_url, wiki_path],
                                capture_output=True,
                                text=True,
                                timeout=300
                            )
                        size_synced += self._get_directory_size(wiki_path)
                        self.log(f"Wiki backed up for {repo}")
                    except:
                        self.log(f"No wiki found for {repo}")

            except subprocess.TimeoutExpired:
                self.log(f"ERROR: Timeout backing up {repo}")
                logger.error(f"Timeout backing up {repo}")
            except Exception as e:
                self.log(f"ERROR backing up {repo}: {str(e)}")
                logger.error(f"Error backing up {repo}: {e}")

        return {
            'files_synced': files_synced,
            'size_synced': size_synced,
            'logs': self.get_logs()
        }

    def _build_repo_url(self, platform, repo, token, host=''):
        """Build repository URL based on platform"""
        if platform == 'gitlab-selfhosted' and host:
            return f"https://oauth2:{token}@{host}/{repo}.git"
        elif platform in ['gitea', 'forgejo'] and host:
            return f"https://{token}@{host}/{repo}.git"
        elif platform == 'gitlab':
            return f"https://oauth2:{token}@gitlab.com/{repo}.git"
        elif platform == 'bitbucket':
            return f"https://x-token-auth:{token}@bitbucket.org/{repo}.git"
        elif platform == 'codeberg':
            return f"https://{token}@codeberg.org/{repo}.git"
        else:
            # Generic format
            return f"https://{token}@{host}/{repo}.git"


# Platform-specific convenience classes
class GitLabBackup(GitBackup):
    """GitLab repository backup handler"""
    def __init__(self, source_config, dest_path):
        if 'platform' not in source_config:
            source_config['platform'] = 'gitlab'
        super().__init__(source_config, dest_path)


class GiteaBackup(GitBackup):
    """Gitea repository backup handler"""
    def __init__(self, source_config, dest_path):
        if 'platform' not in source_config:
            source_config['platform'] = 'gitea'
        super().__init__(source_config, dest_path)


class ForgejoBackup(GitBackup):
    """Forgejo repository backup handler"""
    def __init__(self, source_config, dest_path):
        if 'platform' not in source_config:
            source_config['platform'] = 'forgejo'
        super().__init__(source_config, dest_path)


class BitbucketBackup(GitBackup):
    """Bitbucket repository backup handler"""
    def __init__(self, source_config, dest_path):
        if 'platform' not in source_config:
            source_config['platform'] = 'bitbucket'
        super().__init__(source_config, dest_path)


class CodebergBackup(GitBackup):
    """Codeberg repository backup handler"""
    def __init__(self, source_config, dest_path):
        if 'platform' not in source_config:
            source_config['platform'] = 'codeberg'
        super().__init__(source_config, dest_path)
