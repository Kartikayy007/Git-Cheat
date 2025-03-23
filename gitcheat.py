import os
import subprocess
import shutil
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

def run_command(command, exit_on_error=True):
    """Run a shell command and handle errors."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Error: {result.stderr}")
        if exit_on_error:
            exit(1)
    return result.stdout.strip()

def ensure_git_filter_repo():
    """Ensures that git-filter-repo is installed."""
    logging.info("Checking for git-filter-repo...")
    result = run_command("git filter-repo --help", exit_on_error=False)
    if "usage: git-filter-repo" not in result:
        logging.info("git-filter-repo not found. Installing...")
        run_command("pip install git-filter-repo")

def validate_repo_url(url):
    """Validate the repository URL format."""
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("git@")):
        logging.error(f"Invalid repository URL: {url}")
        exit(1)

def extract_repo_name(url):
    """Extract the repository name from a Git URL."""
    match = re.search(r"/([^/]+?)(\.git)?$", url)
    if match:
        return match.group(1).replace(".git", "")
    logging.error(f"Could not extract repository name from URL: {url}")
    exit(1)

def transfer_repo(old_repo_url, new_repo_url, new_author_name, new_author_email):
    """Transfers all branches from the old repo to the new repo with updated authorship."""
    try:
        validate_repo_url(old_repo_url)
        validate_repo_url(new_repo_url)

        repo_name = extract_repo_name(old_repo_url)
        bare_repo = f"{repo_name}.git"

        logging.info("Cloning the repository...")
        run_command(f"git clone --bare {old_repo_url}")

        os.chdir(bare_repo)

        ensure_git_filter_repo()

        logging.info("Rewriting commit authorship...")
        run_command(f'git filter-repo --commit-callback "commit.author_name = commit.committer_name = b\'{new_author_name}\'; commit.author_email = commit.committer_email = b\'{new_author_email}\'"')

        logging.info("Adding new repository remote...")
        run_command(f"git remote add new-origin {new_repo_url}")

        logging.info("Pushing all branches and tags to the new repository...")
        run_command("git push --mirror new-origin")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        exit(1)

    finally:
        os.chdir("..")
        shutil.rmtree(bare_repo, ignore_errors=True)
        logging.info("✅ Repository transfer complete!")

if __name__ == "__main__":
    print(r"""
       ____   ___   _____            ____   _   _   _____      _      _____ 
      / ___| |_ _| |_   _|          / ___| | | | | | ____|    / \    |_   _|
     | |  _   | |    | |    _____  | |     | |_| | |  _|     / _ \     | |  
     | |_| |  | |    | |   |_____| | |___  |  _  | | |___   / ___ \    | |  
      \____| |___|   |_|            \____| |_| |_| |_____| /_/   \_\   |_|  
    """ )
    old_repo_url = input("Enter the URL of the old repository: ").strip()
    new_repo_url = input("Enter the URL of the new repository: ").strip()
    new_author_name = input("Enter the new author's name: ").strip()
    new_author_email = input("Enter the new author's email: ").strip()

    transfer_repo(old_repo_url, new_repo_url, new_author_name, new_author_email)
