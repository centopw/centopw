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
from collections import Counter
import base64

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

# Get repo information
repos = user.get_repos()
repo_list = list(repos)

# Count statistics
data["REPO_COUNT"] = user.public_repos
data["STAR_COUNT"] = sum(repo.stargazers_count for repo in repo_list)

# Function to generate an ASCII activity graph based on actual commit data
def generate_activity_graph(username, token, days=30):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get user's events
    url = f'https://api.github.com/users/{username}/events'
    response = requests.get(url, headers=headers)
    events = response.json()
    
    # Filter push events (commits)
    push_events = [event for event in events if event['type'] == 'PushEvent']
    
    # Create a dict of dates and commit counts
    today = datetime.datetime.now().date()
    start_date = today - datetime.timedelta(days=days)
    
    # Initialize activity dictionary with zeros for all days
    activity_dict = {(start_date + datetime.timedelta(days=i)).strftime('%Y-%m-%d'): 0 
                     for i in range(days + 1)}
    
    # Count commits per day
    for event in push_events:
        date = datetime.datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        if date in activity_dict:
            # Count number of commits in this push
            activity_dict[date] += len(event['payload'].get('commits', []))
    
    # Convert to a normalized activity level (0-7 for GitHub-style graph)
    activity_values = list(activity_dict.values())
    max_activity = max(activity_values) if max(activity_values) > 0 else 1
    normalized_activity = [min(7, int((count / max_activity) * 7)) for count in activity_values]
    
    # Generate the ASCII graph
    height = 7
    width = len(normalized_activity)
    graph = []
    
    # Create the graph from bottom to top
    for h in range(height, 0, -1):
        line = ""
        for a in normalized_activity:
            if a >= h:
                line += "█"
            else:
                line += " "
        graph.append(line)
    
    # Add bottom axis
    axis = "─" * width
    
    # Add dates indicators (first and last date)
    date_line = f"{list(activity_dict.keys())[0]}{''.center(width-20)}{list(activity_dict.keys())[-1]}"
    
    # Combine everything
    result = "\n".join(graph) + "\n" + axis + "\n" + date_line
    return result

data["ACTIVITY_GRAPH"] = generate_activity_graph(github_username, github_token)

# Count total commits across all repositories
def count_user_commits(username, token):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Start with events API for recent commits
    url = f'https://api.github.com/users/{username}/events'
    response = requests.get(url, headers=headers)
    events = response.json()
    
    # Count commits from events
    commit_count = 0
    for event in events:
        if event['type'] == 'PushEvent':
            commit_count += len(event['payload'].get('commits', []))
    
    # For older data, we need to go through repositories
    # Get user's repositories
    repos_url = f'https://api.github.com/users/{username}/repos?per_page=100'
    response = requests.get(repos_url, headers=headers)
    repos = response.json()
    
    # For each repo, get commit statistics
    for repo in repos:
        # Skip forks to avoid double counting
        if repo.get('fork', False):
            continue
            
        # Get commits for this repo
        commits_url = f"https://api.github.com/repos/{username}/{repo['name']}/commits?author={username}&per_page=1"
        commit_response = requests.get(commits_url, headers=headers)
        
        # Extract the commit count from Link header if available
        if 'Link' in commit_response.headers:
            link_header = commit_response.headers['Link']
            if 'rel="last"' in link_header:
                # Extract the page number from the Link header
                match = re.search(r'page=(\d+)>; rel="last"', link_header)
                if match:
                    repo_commit_count = int(match.group(1))
                    commit_count += repo_commit_count
        else:
            # If no Link header, count the commits in the response
            repo_commits = commit_response.json()
            if isinstance(repo_commits, list):
                commit_count += len(repo_commits)
    
    return commit_count

data["COMMIT_COUNT"] = str(count_user_commits(github_username, github_token))

# Count pull requests
def count_pull_requests(username, token):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Search for PRs created by the user
    search_url = f'https://api.github.com/search/issues?q=author:{username}+type:pr'
    response = requests.get(search_url, headers=headers)
    search_results = response.json()
    
    return search_results.get('total_count', 0)

data["PR_COUNT"] = str(count_pull_requests(github_username, github_token))

# Count issues
def count_issues(username, token):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Search for issues created by the user
    search_url = f'https://api.github.com/search/issues?q=author:{username}+type:issue'
    response = requests.get(search_url, headers=headers)
    search_results = response.json()
    
    return search_results.get('total_count', 0)

data["ISSUE_COUNT"] = str(count_issues(github_username, github_token))

# Count contributions to other repositories
def count_contributions(username, token):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get user's events
    url = f'https://api.github.com/users/{username}/events'
    response = requests.get(url, headers=headers)
    events = response.json()
    
    # Find unique repositories that aren't owned by the user
    contributed_repos = set()
    for event in events:
        repo_name = event['repo']['name']
        if not repo_name.startswith(f"{username}/"):
            contributed_repos.add(repo_name)
    
    return len(contributed_repos)

data["CONTRIB"] = str(count_contributions(github_username, github_token))

# Get latest commit dates for projects
def get_latest_commit_date(repo):
    try:
        latest_commits = list(repo.get_commits(sha=repo.default_branch))
        if latest_commits:
            return latest_commits[0].commit.author.date.strftime("%b %d")
        return "N/A"
    except Exception as e:
        print(f"Error getting commits for {repo.name}: {e}")
        return "N/A"

try:
    tanhiep_repo = g.get_repo(f"{github_username}/tanhiep.dev")
    data["SITE_COMMIT"] = get_latest_commit_date(tanhiep_repo)
except Exception as e:
    print(f"Error accessing personal site repo: {e}")
    data["SITE_COMMIT"] = "N/A"

# Get current projects (based on recent activity)
def get_recent_projects(username, token, count=3):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get user's events
    url = f'https://api.github.com/users/{username}/events'
    response = requests.get(url, headers=headers)
    events = response.json()
    
    # Extract repositories with recent commits
    recent_repos = []
    for event in events:
        if event['type'] == 'PushEvent':
            repo_name = event['repo']['name'].split('/')[1]  # Extract repo name without username
            repo_date = datetime.datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            
            # Check if repo is already in the list
            existing = next((r for r in recent_repos if r['name'] == repo_name), None)
            if existing:
                # Update date if this one is more recent
                if repo_date > existing['date']:
                    existing['date'] = repo_date
            else:
                recent_repos.append({
                    'name': repo_name,
                    'date': repo_date
                })
    
    # Sort by most recent activity
    recent_repos.sort(key=lambda x: x['date'], reverse=True)
    
    # Return the top repositories
    return recent_repos[:count]

recent_projects = get_recent_projects(github_username, github_token)

# Add project data to the data dictionary
if recent_projects:
    data["NEW_PROJECT"] = recent_projects[0]['name']
    data["NEW_COMMIT"] = recent_projects[0]['date'].strftime("%b %d")
    
    # Add data for specific project types if available
    ai_project = next((p for p in recent_projects if any(kw in p['name'].lower() for kw in 
                       ['ai', 'ml', 'machine', 'learning', 'neural', 'deep'])), None)
    if ai_project:
        data["AI_COMMIT"] = ai_project['date'].strftime("%b %d")
    else:
        data["AI_COMMIT"] = "N/A"
        
    react_project = next((p for p in recent_projects if any(kw in p['name'].lower() for kw in 
                          ['react', 'frontend', 'web', 'ui'])), None)
    if react_project:
        data["REACT_COMMIT"] = react_project['date'].strftime("%b %d")
    else:
        data["REACT_COMMIT"] = "N/A"
else:
    # Fallback if no recent projects found
    data["NEW_PROJECT"] = "N/A"
    data["NEW_COMMIT"] = "N/A"
    data["AI_COMMIT"] = "N/A"
    data["REACT_COMMIT"] = "N/A"

# Analyze repos for languages and tools
def analyze_repo_languages(repos):
    language_counter = Counter()
    
    for repo in repos:
        # Skip forks to focus on original work
        if repo.fork:
            continue
            
        # Add repo language
        if repo.language:
            language_counter[repo.language] += 1
        
        # Try to get more detailed language breakdown
        try:
            languages = repo.get_languages()
            for lang, bytes_count in languages.items():
                language_counter[lang] += bytes_count
        except Exception as e:
            print(f"Error getting languages for {repo.name}: {e}")
    
    # Return most common languages
    return language_counter.most_common(10)

# Detect frameworks and tools from repository contents
def detect_frameworks_and_tools(repos, token):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Framework and tool detection patterns
    framework_patterns = {
        'React': ['react', 'jsx', 'tsx'],
        'Next.js': ['next.config.js', 'nextjs'],
        'Vue.js': ['vue.js', 'vue.config.js', 'vuejs'],
        'Angular': ['angular.json', 'ngx'],
        'Django': ['django', 'wsgi.py', 'asgi.py'],
        'Flask': ['flask', 'app.py', 'wsgi.py'],
        'Express': ['express', 'app.js', 'server.js'],
        'Spring Boot': ['spring-boot', 'application.properties'],
        'Laravel': ['laravel', 'artisan'],
        'Svelte': ['svelte.config.js'],
        'Node.js': ['package.json', 'node_modules'],
        'TensorFlow': ['tensorflow', 'tf.'],
        'PyTorch': ['torch', 'pytorch']
    }
    
    tool_patterns = {
        'Docker': ['dockerfile', 'docker-compose'],
        'Kubernetes': ['kubernetes', 'k8s', 'helm'],
        'AWS': ['aws', 'amazon web services', 'cloudformation'],
        'GCP': ['gcp', 'google cloud'],
        'Firebase': ['firebase', 'firestore'],
        'GitHub Actions': ['.github/workflows'],
        'Jenkins': ['jenkinsfile'],
        'Terraform': ['terraform', '.tf'],
        'Jest': ['jest.config', 'test.js'],
        'Pytest': ['pytest', 'test_'],
        'Webpack': ['webpack.config'],
        'Vite': ['vite.config'],
        'Nginx': ['nginx.conf'],
        'GraphQL': ['graphql', 'apollo'],
        'TypeScript': ['tsconfig.json', '.ts', '.tsx'],
        'CI/CD': ['.github/workflows', '.gitlab-ci.yml', 'jenkins']
    }
    
    frameworks_found = Counter()
    tools_found = Counter()
    
    for repo in repos:
        # Skip forks
        if repo.fork:
            continue
            
        try:
            # Check root directory for common config files
            contents = repo.get_contents("")
            file_list = [content.name.lower() for content in contents if content.type == "file"]
            
            # Check for package.json to detect frontend frameworks
            package_json = next((content for content in contents if content.name == "package.json"), None)
            if package_json:
                content = repo.get_contents(package_json.path).decoded_content.decode('utf-8')
                try:
                    package_data = json.loads(content)
                    dependencies = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                    
                    # Check dependencies for frameworks
                    if 'react' in dependencies:
                        frameworks_found['React'] += 5
                    if 'next' in dependencies:
                        frameworks_found['Next.js'] += 5
                    if 'vue' in dependencies:
                        frameworks_found['Vue.js'] += 5
                    if '@angular/core' in dependencies:
                        frameworks_found['Angular'] += 5
                    if 'svelte' in dependencies:
                        frameworks_found['Svelte'] += 5
                    if 'express' in dependencies:
                        frameworks_found['Express'] += 5
                    
                    # Check for testing frameworks
                    if 'jest' in dependencies:
                        tools_found['Jest'] += 3
                    if 'webpack' in dependencies:
                        tools_found['Webpack'] += 3
                    if 'vite' in dependencies:
                        tools_found['Vite'] += 3
                except json.JSONDecodeError:
                    pass
            
            # Check for requirements.txt or pyproject.toml for Python frameworks
            python_deps = next((content for content in contents if content.name in 
                               ["requirements.txt", "pyproject.toml", "Pipfile"]), None)
            if python_deps:
                content = repo.get_contents(python_deps.path).decoded_content.decode('utf-8')
                
                if 'django' in content.lower():
                    frameworks_found['Django'] += 5
                if 'flask' in content.lower():
                    frameworks_found['Flask'] += 5
                if 'tensorflow' in content.lower() or 'tf' in content.lower():
                    frameworks_found['TensorFlow'] += 5
                if 'torch' in content.lower() or 'pytorch' in content.lower():
                    frameworks_found['PyTorch'] += 5
                if 'pytest' in content.lower():
                    tools_found['Pytest'] += 3
            
            # Check for Docker
            if any(docker_file in file_list for docker_file in ['dockerfile', 'docker-compose.yml', 'docker-compose.yaml']):
                tools_found['Docker'] += 5
            
            # Check for CI/CD
            if '.github' in [content.name for content in contents if content.type == "dir"]:
                workflows_path = f"{repo.full_name}/contents/.github/workflows"
                workflows_url = f"https://api.github.com/repos/{workflows_path}"
                workflows_response = requests.get(workflows_url, headers=headers)
                if workflows_response.status_code == 200:
                    tools_found['GitHub Actions'] += 5
                    tools_found['CI/CD'] += 3
            
            # Check for other tool config files
            if any(tf_file.endswith('.tf') for tf_file in file_list):
                tools_found['Terraform'] += 5
            
            if 'tsconfig.json' in file_list:
                tools_found['TypeScript'] += 5
            
            # Check for Kubernetes
            if any(k8s_file in file_list for k8s_file in ['k8s', 'kubernetes', 'helm', 'chart.yaml']):
                tools_found['Kubernetes'] += 5
                
        except Exception as e:
            print(f"Error analyzing repo {repo.name}: {e}")
    
    return frameworks_found.most_common(5), tools_found.most_common(5)

# Get data about languages, frameworks and tools
languages = analyze_repo_languages(repo_list)
top_languages = [lang[0] for lang in languages[:5]]
data["LANGUAGES"] = ", ".join(top_languages)

frameworks, tools = detect_frameworks_and_tools(repo_list, github_token)
data["FRAMEWORKS"] = ", ".join([framework[0] for framework in frameworks])
data["TOOLS"] = ", ".join([tool[0] for tool in tools])

# Determine what the user is currently learning
def determine_learning_focus(repos, recent_projects):
    # Technologies commonly associated with learning paths
    learning_areas = {
        'DevOps': ['docker', 'kubernetes', 'jenkins', 'cicd', 'terraform', 'ansible'],
        'Cloud Architecture': ['aws', 'gcp', 'azure', 'cloud', 'serverless', 'lambda'],
        'System Design': ['architecture', 'system-design', 'distributed', 'scalable'],
        'Microservices': ['microservice', 'service-mesh', 'api-gateway', 'grpc'],
        'AI/ML': ['ai', 'ml', 'machine-learning', 'deep-learning', 'neural', 'tensorflow', 'pytorch'],
        'Blockchain': ['blockchain', 'web3', 'ethereum', 'solidity', 'crypto'],
        'Mobile Development': ['android', 'ios', 'flutter', 'react-native', 'mobile'],
        'Game Development': ['game', 'unity', 'unreal', 'godot'],
        'UI/UX Design': ['ui', 'ux', 'design', 'figma', 'sketch', 'adobe']
    }
    
    # Check recent projects and READMEs for learning indicators
    learning_matches = Counter()
    
    # First check names of recent projects
    for project in recent_projects:
        project_name_lower = project['name'].lower()
        for area, keywords in learning_areas.items():
            if any(keyword in project_name_lower for keyword in keywords):
                learning_matches[area] += 3
    
    # Then check READMEs of repos for learning mentions
    for repo in repos:
        if repo.fork:
            continue
            
        try:
            readme = None
            for readme_name in ['README.md', 'readme.md', 'Readme.md', 'README.txt']:
                try:
                    readme = repo.get_contents(readme_name)
                    break
                except:
                    continue
                    
            if readme:
                content = readme.decoded_content.decode('utf-8').lower()
                
                # Look for learning indicators
                learning_indicators = ['learning', 'studying', 'experimenting with', 'exploring']
                
                for area, keywords in learning_areas.items():
                    for keyword in keywords:
                        if keyword in content:
                            # Higher score if near learning indicators
                            for indicator in learning_indicators:
                                if indicator in content and abs(content.find(indicator) - content.find(keyword)) < 100:
                                    learning_matches[area] += 2
                            # Regular score for mention
                            learning_matches[area] += 1
                            
        except Exception as e:
            print(f"Error reading README for {repo.name}: {e}")
    
    # Check creation dates to prioritize newer interests
    for repo in repos:
        if repo.fork:
            continue
            
        # Give preference to repos created in the last 3 months
        if (datetime.datetime.now().replace(tzinfo=None) - 
            repo.created_at.replace(tzinfo=None)).days < 90:
            
            repo_name_lower = repo.name.lower()
            for area, keywords in learning_areas.items():
                if any(keyword in repo_name_lower for keyword in keywords):
                    learning_matches[area] += 2
    
    # Return the top learning focus, or a reasonable default
    if learning_matches:
        return learning_matches.most_common(1)[0][0]
    return random.choice(list(learning_areas.keys()))

data["CURRENT_LEARNING"] = determine_learning_focus(repo_list, recent_projects)

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

# Add a fun ASCII art
def generate_ascii_art(username):
    try:
        ascii_art = pyfiglet.figlet_format(username, font="slant")
        return ascii_art
    except:
        return cowsay.get_output_string('cow', f"Hello, I'm {username}!")

data["ASCII_ART"] = generate_ascii_art(github_username)

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
