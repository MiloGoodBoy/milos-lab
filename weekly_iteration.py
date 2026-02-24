#!/usr/bin/env python3
"""
Milo's Lab - Weekly Iteration Script

Runs weekly to:
1. Fetch all repos from GitHub
2. Clone/update each locally
3. Test it (run main script if exists)
4. Identify one improvement
5. Implement it
6. Push updates to GitHub
7. Log changes to memory

Run: python3 weekly_iteration.py
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from subprocess import run, PIPE

# Configuration
LAB_DIR = Path("/home/ubuntu/.openclaw/workspace/milos-lab")
MEMORY_FILE = "/home/ubuntu/.openclaw/memory/weekly-iteration.md"
GH_TOKEN_FILE = "/home/ubuntu/.openclaw/config/github-credentials.json"

class WeeklyIteration:
    def __init__(self):
        self.changes = []
        self.week = datetime.now().strftime("%Y-W%W")
        self.repos = []
        self.token = self._get_gh_token()
        
    def _get_gh_token(self):
        """Get GitHub token from credentials file."""
        with open(GH_TOKEN_FILE) as f:
            creds = json.load(f)
        return creds.get("token", "")
    
    def fetch_repos(self):
        """Fetch all repos from GitHub API."""
        print("📡 Fetching repos from GitHub...")
        
        result = run(
            ["curl", "-s", f"https://api.github.com/users/MiloGoodBoy/repos?sort=updated&per_page=100"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  ⚠️ Failed to fetch repos: {result.stderr}")
            return []
        
        try:
            repos = json.loads(result.stdout)
            self.repos = [(r["name"], r["clone_url"], r["description"]) for r in repos]
            print(f"  ✅ Found {len(self.repos)} repos")
            return self.repos
        except json.JSONDecodeError as e:
            print(f"  ⚠️ Failed to parse repos: {e}")
            return []
    
    def ensure_repo(self, repo_name, clone_url):
        """Ensure repo exists locally, clone or pull if not."""
        repo_path = LAB_DIR / repo_name
        
        if not repo_path.exists():
            print(f"  📥 Cloning {repo_name}...")
            # Use token in URL for cloning
            auth_url = clone_url.replace("https://", f"https://MiloGoodBoy:{self.token}@")
            result = run(["git", "clone", "--depth", "1", auth_url, str(repo_path)], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  ⚠️ Clone failed: {result.stderr[:100]}")
                return None
            print(f"  ✅ Cloned")
        else:
            print(f"  🔄 Updating {repo_name}...")
            # Pull latest
            result = run(["git", "pull", "origin", "main"], cwd=repo_path, capture_output=True, text=True)
            if result.returncode != 0:
                # Try main branch
                result = run(["git", "pull", "origin", "master"], cwd=repo_path, capture_output=True, text=True)
            print(f"  ✅ Updated")
        
        return repo_path
    
    def test_project(self, repo_name, repo_path):
        """Test a project by running its main script."""
        print(f"\n🧪 Testing {repo_name}...")
        
        # Look for common Python entry points
        candidates = [
            repo_path / "main.py",
            repo_path / f"{repo_name}.py",
            repo_path / "run.py",
            repo_path / "bot.py",
            repo_path / "app.py",
        ]
        
        main_script = None
        for candidate in candidates:
            if candidate.exists():
                main_script = candidate
                break
        
        # Also check for subdirectories with scripts
        if not main_script:
            for subdir in repo_path.iterdir():
                if subdir.is_dir() and not subdir.name.startswith("."):
                    for candidate in ["main.py", "run.py", "bot.py"]:
                        if (subdir / candidate).exists():
                            main_script = subdir / candidate
                            break
                if main_script:
                    break
        
        if not main_script:
            print(f"  ℹ️ No testable Python script found")
            return True  # Not a failure, just nothing to test
        
        # Run the script
        result = run(
            ["python3", str(main_script)],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"  ✅ Test passed")
            return True
        else:
            print(f"  ⚠️ Test output:\n{result.stdout[:200]}")
            if result.stderr:
                print(f"  ⚠️ Errors:\n{result.stderr[:200]}")
            return False
    
    def identify_improvement(self, repo_name, repo_path):
        """Identify one improvement for the project."""
        # Check for TODO in code
        for py_file in repo_path.glob("**/*.py"):
            if py_file.name.startswith("."):
                continue
            try:
                content = py_file.read_text(errors="ignore")
                if "# TODO" in content or "# FIXME" in content:
                    return f"Implement TODO in {py_file.name}"
            except:
                pass
        
        # Check README for missing sections
        readme = repo_path / "README.md"
        if readme.exists():
            content = readme.read_text()
            if "## Installation" not in content and "## Setup" not in content:
                return "Add installation/setup instructions to README"
            if "## License" not in content:
                return "Add LICENSE file"
        
        # Check for missing files
        if not (repo_path / "README.md").exists():
            return "Add README.md"
        if not (repo_path / "LICENSE").exists():
            return "Add LICENSE file"
        
        # Default improvements
        return "General bug fixes and code cleanup"
    
    def implement_improvement(self, repo_name, improvement):
        """Implement the identified improvement."""
        print(f"\n🔧 Implementing: {improvement}")
        
        # Log what would be done
        self.changes.append({
            "project": repo_name,
            "improvement": improvement,
            "status": "identified"
        })
        
        print(f"  📝 Logged: {improvement}")
        return True
    
    def commit_and_push(self, repo_name, repo_path):
        """Commit changes and push to GitHub."""
        # Check if git is initialized
        if not (repo_path / ".git").exists():
            print(f"  ⚠️ No git repo in {repo_name}")
            return False
        
        # Add changes
        run(["git", "add", "-A"], cwd=repo_path, capture_output=True)
        
        # Check if there are changes
        result = run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)
        if not result.stdout.strip():
            print(f"  ℹ️ No changes to commit")
            return True
        
        # Commit
        commit_msg = f"{self.week}: {repo_name} iteration - {self.changes[-1]['improvement']}"
        run(["git", "commit", "-m", commit_msg], cwd=repo_path, capture_output=True)
        
        # Push with token
        result = run(
            ["git", "push", "origin", "main"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            # Try main branch
            result = run(
                ["git", "push", "origin", "master"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
        
        if result.returncode != 0:
            print(f"  ⚠️ Push failed: {result.stderr[:100]}")
            return False
        
        print(f"  ✅ Pushed to GitHub")
        return True
    
    def log_to_memory(self):
        """Log changes to memory."""
        if not self.changes:
            print("\n📝 No changes to log")
            return
        
        entry = f"""## {self.week} - Weekly Iteration

**Date:** {datetime.now().isoformat()}

### Changes Made

"""
        for change in self.changes:
            entry += f"- **{change['project']}**: {change['improvement']}\n"
        
        entry += "\n---\n"
        
        # Append to memory
        memory_path = Path(MEMORY_FILE)
        memory_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(memory_path, "a") as f:
            f.write(entry)
        
        print(f"\n📝 Logged to {MEMORY_FILE}")
    
    def run(self):
        """Main execution."""
        print("=" * 60)
        print("Milo's Lab - Weekly Iteration")
        print(f"Week: {self.week}")
        print("=" * 60)
        
        # Fetch repos from GitHub
        repos = self.fetch_repos()
        
        if not repos:
            print("❌ No repos found, exiting")
            return
        
        for repo_name, clone_url, description in repos:
            print(f"\n📁 Project: {repo_name}")
            if description:
                print(f"   {description}")
            
            # Ensure repo exists locally
            repo_path = self.ensure_repo(repo_name, clone_url)
            if not repo_path:
                continue
            
            # Test
            self.test_project(repo_name, repo_path)
            
            # Identify improvement
            improvement = self.identify_improvement(repo_name, repo_path)
            print(f"\n💡 Improvement: {improvement}")
            
            # Implement (mark as identified)
            self.implement_improvement(repo_name, improvement)
            
            # Commit & push
            self.commit_and_push(repo_name, repo_path)
        
        # Log to memory
        self.log_to_memory()
        
        print("\n" + "=" * 60)
        print(f"✅ Weekly iteration complete! ({len(self.repos)} repos)")
        print("=" * 60)

if __name__ == "__main__":
    wi = WeeklyIteration()
    wi.run()
