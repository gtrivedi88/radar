"""Git operations service"""

import subprocess
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class GitOpsService:
    """Handles Git operations for Radar state management"""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    async def preflight_check(self) -> Dict[str, Any]:
        """Run pre-flight git check (R12: avoid dirty state conflicts)"""
        logger.info("Running git preflight check")

        result = {
            "success": False,
            "clean_state": False,
            "upstream_synced": False,
            "message": "",
        }

        try:
            # Check if we're in a git repository
            if not (self.repo_path / ".git").exists():
                result["message"] = f"{self.repo_path} is not a git repository"
                return result

            # Check for upstream configuration
            upstream_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if upstream_result.returncode != 0:
                # No upstream configured - treat as success for local-only repos
                result["success"] = True
                result["clean_state"] = True
                result["upstream_synced"] = True
                result["message"] = "No upstream configured (local-only repo)"
                return result

            # Pull with rebase to sync with upstream
            pull_result = subprocess.run(
                ["git", "pull", "--rebase"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if pull_result.returncode != 0:
                result["message"] = (
                    "git pull --rebase failed. Resolve conflicts or push pending edits "
                    f"before re-running.\n\nstdout:\n{pull_result.stdout}\n"
                    f"stderr:\n{pull_result.stderr}"
                )
                return result

            result["success"] = True
            result["clean_state"] = True
            result["upstream_synced"] = True
            result["message"] = "Git preflight check passed"

        except Exception as e:
            result["message"] = f"Git preflight check failed: {e}"
            logger.error(result["message"])

        return result

    async def commit_changes(self, files: list[str], message: str) -> Dict[str, Any]:
        """Commit specified files with given message"""
        logger.info(f"Committing changes: {message}")

        result = {
            "success": False,
            "commit_hash": None,
            "message": "",
        }

        try:
            # Add files
            add_result = subprocess.run(
                ["git", "add"] + files,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if add_result.returncode != 0:
                result["message"] = f"git add failed: {add_result.stderr}"
                return result

            # Commit
            commit_result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if commit_result.returncode != 0:
                result["message"] = f"git commit failed: {commit_result.stderr}"
                return result

            # Get commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            result["success"] = True
            result["commit_hash"] = hash_result.stdout.strip() if hash_result.returncode == 0 else None
            result["message"] = "Changes committed successfully"

        except Exception as e:
            result["message"] = f"Commit failed: {e}"
            logger.error(result["message"])

        return result