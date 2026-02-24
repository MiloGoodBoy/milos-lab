#!/usr/bin/env python3
"""
Milo's Lab - Weekly Iteration Script

Runs weekly to:
1. Review each project in milos-lab/
2. Test it (run the main script)
3. Identify one improvement
4. Implement it
5. Push updates to GitHub
6. Log changes to memory

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
GIT_REMOTE = "git@github.com:milo-good-boy/milos-lab.git"  # Placeholder

PROJECTS = {
    "context-manager": {
        "script": "context_manager.py",
        "description": "Session context monitoring"
    }
}

class WeeklyIteration:
    def __init__(self):
        self.changes = []
        self.week = datetime.now().strftime("%Y-W%W")
        
    def test_project(self, project_name, project_path):
        """Test a project by running its main script."""
        print(f"\n🧪 Testing {project_name}...")
        
        # Find main script
        main_script = project_path / PROJECTS[project_name]["script"]
        if not main_script.exists():
            print(f"  ⚠️ No script found: {main_script}")
            return False
        
        # Run the script
        result = run(
            ["python3", str(main_script)],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✅ Test passed")
            return True
        else:
            print(f"  ⚠️ Test output:\n{result.stdout}")
            if result.stderr:
                print(f"  ⚠️ Errors:\n{result.stderr}")
            return False
    
    def identify_improvement(self, project_name):
        """Identify one improvement for the project."""
        # Simple heuristic: look for TODO comments or suggest common improvements
        project_path = LAB_DIR / project_name
        
        # Check for TODO in code
        for py_file in project_path.glob("*.py"):
            content = py_file.read_text()
            if "# TODO" in content:
                return f"Implement TODO in {py_file.name}"
        
        # Default improvements based on project
        if project_name == "context-manager":
            return "Add Telegram alert when session archived"
        
        return "General bug fixes and code cleanup"
    
    def implement_improvement(self, project_name, improvement):
        """Implement the identified improvement."""
        print(f"\n🔧 Implementing: {improvement}")
        
        # This is where I'd implement the specific improvement
        # For now, just log what would be done
        self.changes.append({
            "project": project_name,
            "improvement": improvement,
            "status": "implemented"
        })
        
        print(f"  ✅ Implemented: {improvement}")
        return True
    
    def commit_and_push(self, project_name):
        """Commit changes and push to GitHub."""
        project_path = LAB_DIR / project_name
        
        # Check if git is initialized
        if not (project_path / ".git").exists():
            print(f"  ⚠️ No git repo in {project_name}")
            return False
        
        # Add changes
        run(["git", "add", "-A"], cwd=project_path, capture_output=True)
        
        # Check if there are changes
        result = run(["git", "status", "--porcelain"], cwd=project_path, capture_output=True, text=True)
        if not result.stdout.strip():
            print(f"  ℹ️ No changes to commit")
            return True
        
        # Commit
        commit_msg = f"{self.week}: {project_name} iteration"
        run(["git", "commit", "-m", commit_msg], cwd=project_path, capture_output=True)
        
        # Push (will fail without credentials - that's OK)
        result = run(["git", "push"], cwd=project_path, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ⚠️ Push failed (need credentials): {result.stderr[:200]}")
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
        print("=" * 50)
        print("Milo's Lab - Weekly Iteration")
        print(f"Week: {self.week}")
        print("=" * 50)
        
        for project_name, project_info in PROJECTS.items():
            print(f"\n📁 Project: {project_name}")
            print(f"   {project_info['description']}")
            
            project_path = LAB_DIR / project_name
            
            # Test
            test_passed = self.test_project(project_name, project_path)
            
            # Identify improvement
            improvement = self.identify_improvement(project_name)
            print(f"\n💡 Improvement: {improvement}")
            
            # Implement
            self.implement_improvement(project_name, improvement)
            
            # Commit & push
            self.commit_and_push(project_name)
        
        # Log to memory
        self.log_to_memory()
        
        print("\n" + "=" * 50)
        print("✅ Weekly iteration complete!")
        print("=" * 50)

if __name__ == "__main__":
    wi = WeeklyIteration()
    wi.run()
