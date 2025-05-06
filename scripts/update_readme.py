#!/usr/bin/env python3
"""
Dynamic README Generator for GitHub Profile
Uses GitHub API to fetch real data and update the README.md file
"""

import os
import re
import json
import random
import datetime
import requests
from github import Github
from dateutil.relativedelta import relativedelta
import cowsay
import pyfiglet

# GitHub Authentication
github_token = os.environ.get("GH_TOKEN")
github_username = os.environ.get("GITHUB_USERNAME", "centopw")
g = Github(github_token)
user = g.get_user(github_username)

# Initialize data dictionary
data = {}

# Get current date
data["CURRENT_DATE"] = datetime.datetime.now().strftime("%A, %B %d, %Y - %H:%M:%S UTC")

# Random status messages
status_messages = [
    "Currently building the future, one commit at a time",
    "Debugging the universe since 1999",
    "Teaching computers to think like humans",
    "Converting caffeine into code",
    "Crafting digital experiences that matter",
    "Breaking and rebuilding things to understand them better"
]
data["CURRENT_STATUS"] = random.choice(status_messages)

# Calculate days active
account_created = user.created_at
days_active = (datetime.datetime.now().replace(tzinfo=None) - account_created.replace(tzinfo=None)).days
data["DAYS_ACTIVE"] = days_active

# Generate ASCII activity graph (simplified version)
def generate_ascii_graph():
    # This would normally use actual GitHub activity data
    # For simplicity, we'll generate a random graph
    height = 7
    width = 30
    graph = []
    
    # Generate random activity levels
    activity = [random.randint(0, height) for _ in range(width)]
    
    # Create the graph from bottom to top
    for h in range(height, 0, -1):
        line = ""
        for a in activity:
            if a >= h:
                line += "█"
            else:
                line += " "
        graph.append(line)
    
    # Add bottom axis
    axis = "─" * width
    
    # Combine everything
    result = "\n".join(graph) + "\n" + axis
    return result

data["ACTIVITY_GRAPH"] = generate_ascii_graph()

# Get repo information
repos = user.get_repos()
repo_list = list(repos)

# Count statistics
data["REPO_COUNT"] = user.public_repos
data["STAR_COUNT"] = sum(repo.stargazers_count for repo in repo_list)

# These would normally be calculated from GitHub API
# Using placeholder values for demonstration
data["COMMIT_COUNT"] = "3,500+"
data["PR_COUNT"] = "150+"
data["ISSUE_COUNT"] = "75+"
data["CONTRIB"] = "20+"

# Get latest commit dates for projects
try:
    tanhiep_repo = g.get_repo(f"{github_username}/tanhiep.dev")
    latest_commit = list(tanhiep_repo.get_commits())
    if latest_commit:
        data["SITE_COMMIT"] = latest_commit[0].commit.author.date.strftime("%b %d")
    else:
        data["SITE_COMMIT"] = "N/A"
except:
    data["SITE_COMMIT"] = "N/A"

# Get current projects (this would be more sophisticated in practice)
project_names = ["cloud-native-app", "ml-experiments", "web3-project", "dev-dashboard"]
data["NEW_PROJECT"] = random.choice(project_names)
data["NEW_COMMIT"] = datetime.datetime.now().strftime("%b %d")
data["AI_COMMIT"] = (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 14))).strftime("%b %d")
data["REACT_COMMIT"] = (datetime.datetime.now() - datetime.timedelta(days=random.randint(15, 30))).strftime("%b %d")

# Analyze repos for languages and tools
languages = set()
frameworks = set()
tools = set()

# In practice, this would analyze repo contents and package.json files
# Using placeholder values for demonstration
frameworks_list = ["React", "Node.js", "Express", "Django", "Next.js", "Vue.js", "Flask", "Spring Boot"]
tools_list = ["Git", "Docker", "AWS", "Firebase", "Kubernetes", "Terraform", "CI/CD", "Jest", "Webpack"]
learning_list = ["DevOps", "Cloud Architecture", "System Design", "Microservices", "AI/ML", "Blockchain"]

# Select random items to simulate changing data
data["FRAMEWORKS"] = ", ".join(random.sample(frameworks_list, k=min(4, len(frameworks_list))))
data["TOOLS"] = ", ".join(random.sample(tools_list, k=min(4, len(tools_list))))
data["CURRENT_LEARNING"] = random.choice(learning_list)

# Developer quotes
quotes = [
    "The best way to predict the future is to build it.",
    "Code is like humor. When you have to explain it, it's bad.",
    "First, solve the problem. Then, write the code.",
    "It's not a bug – it's an undocumented feature.",
    "The most disastrous thing that you can ever learn is your first programming language.",
    "Programming isn't about what you know; it's about what you can figure out.",
    "The only way to learn a new programming language is by writing programs in it.",
    "Testing leads to failure, and failure leads to understanding."
]
data["RANDOM_QUOTE"] = random.choice(quotes)

# Read in the template README
with open('README.md', 'r') as file:
    readme = file.read()

# Replace all placeholders
for key, value in data.items():
    placeholder = f"{{{{ {key} }}}}"
    readme = readme.replace(placeholder, str(value))

# Write the updated README
with open('README.md', 'w') as file:
    file.write(readme)

print("README.md updated successfully!")
