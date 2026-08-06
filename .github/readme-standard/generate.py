import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import quote

START = "<!-- interactive-readme-standard:start -->"
END = "<!-- interactive-readme-standard:end -->"
PROFILE_REPOSITORY = "Nischhalsubba/Nischhalsubba"

repository = os.environ["REPOSITORY"]
branch = os.environ["BRANCH_NAME"]
default_branch = os.environ.get("DEFAULT_BRANCH", "main")
repo_name = repository.split("/", 1)[1]
root = Path(".")

if repository == PROFILE_REPOSITORY:
    raise SystemExit("Profile repository is intentionally excluded from README automation.")

IGNORED = {
    ".git", ".next", ".nuxt", ".output", ".venv", "venv", "node_modules",
    "vendor", "dist", "build", "coverage", "target", "__pycache__", ".cache",
    ".turbo", ".idea", ".vscode", ".gradle", ".dart_tool",
}
TEXT_SUFFIXES = {
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".py", ".java", ".kt",
    ".go", ".rs", ".php", ".rb", ".cs", ".cpp", ".c", ".swift", ".dart",
    ".html", ".htm", ".css", ".scss", ".sass", ".vue", ".svelte", ".astro",
    ".sql", ".graphql", ".gql", ".md", ".json", ".yaml", ".yml", ".toml",
}


def add_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def clean_label(value: str) -> str:
    return value.replace('"', "'").replace("[", "(").replace("]", ")").replace("`", "'")


def display_path(path: Path) -> str:
    return f"{path.as_posix()}/" if path.is_dir() else path.as_posix()


def github_path_link(path: str) -> str:
    safe_path = quote(path, safe="/")
    safe_branch = quote(branch, safe="/")
    return f"https://github.com/{repository}/tree/{safe_branch}/{safe_path}"


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def read_text(path: Path, limit: int = 160_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def existing_files(candidates: list[str]) -> list[str]:
    return [name for name in candidates if (root / name).exists()]


def run_git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, check=False, capture_output=True, text=True, timeout=20
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def static_badge(message: str, color: str = "5965F2") -> str:
    msg = quote(message, safe="")
    return f'<img alt="{clean_label(message)}" src="https://img.shields.io/static/v1?label=&message={msg}&color={color}&style=flat-square">'


entries = sorted(
    [p for p in root.iterdir() if p.name not in IGNORED and p.name != "README.md"],
    key=lambda p: (not p.is_dir(), p.name.lower()),
)

frameworks: list[str] = []
commands: list[str] = []
manifest_files: list[str] = []
prerequisites: list[str] = []
project_description = ""
package_manager = ""

package_json = root / "package.json"
if package_json.exists():
    manifest_files.append("package.json")
    package = read_json(package_json)
    project_description = str(package.get("description") or "").strip()
    dependencies: dict = {}
    dependencies.update(package.get("dependencies") or {})
    dependencies.update(package.get("devDependencies") or {})
    scripts = package.get("scripts") or {}
    framework_map = {
        "next": "Next.js", "react": "React", "vue": "Vue", "nuxt": "Nuxt",
        "svelte": "Svelte", "@sveltejs/kit": "SvelteKit", "astro": "Astro",
        "vite": "Vite", "express": "Express", "fastify": "Fastify",
        "@nestjs/core": "NestJS", "electron": "Electron", "tailwindcss": "Tailwind CSS",
        "typescript": "TypeScript", "@strapi/strapi": "Strapi", "gatsby": "Gatsby",
    }
    for dependency, label in framework_map.items():
        if dependency in dependencies:
            add_unique(frameworks, label)
    package_manager = "pnpm" if (root / "pnpm-lock.yaml").exists() else "yarn" if (root / "yarn.lock").exists() else "npm"
    add_unique(prerequisites, "Node.js")
    if package_manager == "pnpm":
        add_unique(prerequisites, "pnpm")
    elif package_manager == "yarn":
        add_unique(prerequisites, "Yarn")
    for script_name in ("dev", "start", "build", "test", "lint", "typecheck", "preview", "format"):
        if script_name in scripts:
            prefix = "pnpm" if package_manager == "pnpm" else "yarn" if package_manager == "yarn" else "npm run"
            command = f"{prefix} {script_name}"
            add_unique(commands, command)

manifest_map = {
    "pyproject.toml": ["Python"], "requirements.txt": ["Python"], "Pipfile": ["Python"],
    "poetry.lock": ["Poetry"], "pom.xml": ["Java", "Maven"],
    "build.gradle": ["Java", "Gradle"], "build.gradle.kts": ["Kotlin", "Gradle"],
    "go.mod": ["Go"], "Cargo.toml": ["Rust", "Cargo"],
    "composer.json": ["PHP", "Composer"], "Gemfile": ["Ruby"],
    "pubspec.yaml": ["Dart", "Flutter"], "Dockerfile": ["Docker"],
    "docker-compose.yml": ["Docker Compose"], "compose.yaml": ["Docker Compose"],
}
for manifest, labels in manifest_map.items():
    if (root / manifest).exists():
        manifest_files.append(manifest)
        for label in labels:
            add_unique(frameworks, label)

if any((root / p).exists() for p in ("pyproject.toml", "requirements.txt", "Pipfile", "manage.py")):
    add_unique(prerequisites, "Python")
if (root / "manage.py").exists():
    add_unique(frameworks, "Django")
    add_unique(commands, "python manage.py runserver")
    add_unique(commands, "python manage.py test")
if (root / "artisan").exists():
    add_unique(frameworks, "Laravel")
    add_unique(commands, "php artisan serve")
if (root / "wp-content").exists() or ((root / "style.css").exists() and (root / "functions.php").exists()):
    add_unique(frameworks, "WordPress")
if (root / "go.mod").exists():
    add_unique(prerequisites, "Go")
    add_unique(commands, "go test ./...")
if (root / "Cargo.toml").exists():
    add_unique(prerequisites, "Rust")
    add_unique(commands, "cargo test")
if (root / "pom.xml").exists():
    add_unique(prerequisites, "Java")
    add_unique(commands, "mvn test")
if (root / "build.gradle").exists() or (root / "build.gradle.kts").exists():
    add_unique(prerequisites, "Java")
    add_unique(commands, "./gradlew test")

extension_labels = {
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".py": "Python", ".java": "Java",
    ".kt": "Kotlin", ".go": "Go", ".rs": "Rust", ".php": "PHP", ".rb": "Ruby",
    ".cs": "C#", ".cpp": "C++", ".c": "C", ".swift": "Swift", ".dart": "Dart",
    ".html": "HTML", ".css": "CSS", ".scss": "Sass", ".sass": "Sass",
    ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro",
}
counts: Counter[str] = Counter()
scanned = 0
all_files: list[str] = []
for current_root, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in IGNORED]
    relative_root = Path(current_root).relative_to(root)
    if len(relative_root.parts) > 5:
        dirs[:] = []
        continue
    for filename in files:
        scanned += 1
        rel = (relative_root / filename).as_posix()
        all_files.append(rel)
        label = extension_labels.get(Path(filename).suffix.lower())
        if label:
            counts[label] += 1
        if scanned >= 12_000:
            break
    if scanned >= 12_000:
        break
for language, _ in counts.most_common(6):
    add_unique(frameworks, language)

lower_files = [f.lower() for f in all_files]


def find_matching(parts: tuple[str, ...], limit: int = 16) -> list[str]:
    matches = []
    for original, lower in zip(all_files, lower_files):
        if any(part in lower for part in parts):
            matches.append(original)
        if len(matches) >= limit:
            break
    return matches


route_roots = existing_files([
    "app", "pages", "routes", "site", "web", "frontend", "client", "src/app",
    "src/pages", "src/routes", "src/screens", "src/views", "templates", "public",
])
route_files = [
    f for f in all_files
    if any(f == r or f.startswith(r.rstrip("/") + "/") for r in route_roots)
    and Path(f).suffix.lower() in {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro", ".php", ".py"}
][:16]

api_paths = existing_files(["api", "server", "backend", "src/api", "src/server", "app/api", "pages/api"])
auth_files = find_matching(("auth", "login", "session", "oauth", "jwt", "permission", "rbac"), 12)
data_paths = existing_files(["db", "database", "models", "migrations", "prisma", "data", "storage", "supabase"])
data_files = find_matching(("schema.prisma", "migration", "/models/", "/model/", "database", "supabase"), 14)
job_files = find_matching(("queue", "worker", "job", "cron", "scheduler", "celery", "bullmq"), 10)
observability_files = find_matching(("sentry", "opentelemetry", "telemetry", "logger", "logging", "analytics"), 10)
test_paths = existing_files(["test", "tests", "spec", "specs", "e2e", "cypress", "playwright"])
security_files = existing_files(["SECURITY.md", ".github/dependabot.yml", ".github/dependabot.yaml", ".github/codeql"])
env_files = [f for f in all_files if Path(f).name.startswith(".env") and Path(f).name != ".env"][:8]
license_files = existing_files(["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"])
codeowner_files = existing_files(["CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"])
contributing_files = existing_files(["CONTRIBUTING.md", ".github/CONTRIBUTING.md"])

deployment_files = existing_files([
    "Dockerfile", "docker-compose.yml", "compose.yaml", "netlify.toml", "vercel.json",
    "render.yaml", "fly.toml", "Procfile", "firebase.json", "wrangler.toml", "railway.json",
])
workflow_dir = root / ".github" / "workflows"
workflow_files = []
if workflow_dir.exists():
    workflow_files = [p.relative_to(root).as_posix() for p in sorted(workflow_dir.glob("*.y*ml"))][:12]
    add_unique(deployment_files, "GitHub Actions")

area_candidates = {
    "Interface": ["app", "pages", "site", "web", "frontend", "client", "public", "templates", "components", "src"],
    "Application logic": ["server", "backend", "api", "services", "service", "lib", "core", "domain"],
    "Data": ["db", "database", "models", "migrations", "prisma", "data", "storage", "supabase"],
    "Quality": ["test", "tests", "spec", "specs", "e2e", "cypress", "playwright"],
    "Documentation": ["docs", "documentation", "examples"],
    "Delivery": [".github", "infra", "infrastructure", "deploy", "deployment", "docker", "scripts"],
}
entry_names = {p.name.lower(): p.name for p in entries}
detected_areas: list[tuple[str, list[str]]] = []
for area, candidates in area_candidates.items():
    matches: list[str] = []
    for candidate in candidates:
        top = candidate.split("/", 1)[0].lower()
        actual = entry_names.get(top)
        if actual and actual not in matches:
            matches.append(actual)
    if matches:
        detected_areas.append((area, matches[:5]))
if not detected_areas:
    detected_areas.append(("Project files", [display_path(p) for p in entries[:5]] or ["README.md"]))

branch_changes: list[str] = []
if branch != default_branch:
    diff = run_git("diff", "--name-only", f"origin/{default_branch}...HEAD")
    branch_changes = [line for line in diff.splitlines() if line.strip()][:20]
branch_role = "Default branch" if branch == default_branch else f"Compared with `{default_branch}`"

if not project_description:
    if route_roots and api_paths:
        project_description = "A full-stack project with interface and server-side application areas detected in this branch."
    elif route_roots:
        project_description = "A web or interface project documented from the files currently present on this branch."
    elif api_paths:
        project_description = "A backend or API-oriented project documented from the files currently present on this branch."
    elif frameworks:
        project_description = f"A {frameworks[0]} project documented from the current branch structure and manifests."
    else:
        project_description = "Branch-specific project documentation generated from the repository structure without inventing missing capabilities."

shown_entries = entries[:18]
repo_lines = ["flowchart TD", f'    ROOT["{clean_label(repo_name)} / {clean_label(branch)}"]']
for index, path in enumerate(shown_entries):
    node = f"P{index}"
    repo_lines.append(f'    ROOT --> {node}["{clean_label(display_path(path))}"]')
if len(entries) > len(shown_entries):
    repo_lines.append(f'    ROOT --> MORE["+ {len(entries) - len(shown_entries)} more top-level entries"]')

architecture_lines = ["flowchart LR", '    USER["User / contributor"]']
previous = "USER"
for index, (area, matches) in enumerate(detected_areas):
    node = f"A{index}"
    architecture_lines.append(f'    {previous} --> {node}["{clean_label(area)}: {clean_label(", ".join(matches))}"]')
    previous = node
if deployment_files:
    architecture_lines.append(f'    {previous} --> DELIVERY["Delivery: {clean_label(", ".join(deployment_files[:5]))}"]')

route_lines = ["flowchart TD", f'    APP["{clean_label(repo_name)}"]']
if route_roots:
    for index, candidate in enumerate(route_roots[:8]):
        route_lines.append(f'    APP --> R{index}["{clean_label(candidate)}"]')
    for index, route_file in enumerate(route_files[:12]):
        parent_index = next((i for i, candidate in enumerate(route_roots[:8]) if route_file == candidate or route_file.startswith(candidate.rstrip("/") + "/")), 0)
        route_lines.append(f'    R{parent_index} --> F{index}["{clean_label(route_file)}"]')
else:
    route_lines.extend(['    APP --> SOURCE["No conventional route directory detected"]', '    SOURCE --> GUIDE["Use the repository and architecture maps below"]'])

request_lines = [
    "sequenceDiagram", "    autonumber", "    actor U as User / client",
    "    participant I as Interface", "    participant A as API / application", "    participant D as Data layer",
    "    U->>I: Trigger action", "    I->>A: Send validated request", "    A->>D: Read or write data",
    "    D-->>A: Return result", "    A-->>I: Return response", "    I-->>U: Render success or error state",
]
auth_lines = [
    "flowchart LR", '    USER["User"] --> SIGNIN["Sign-in or identity step"]',
    '    SIGNIN --> VERIFY["Verify credentials / session"]', '    VERIFY --> AUTHORIZE["Resolve permissions"]',
    '    AUTHORIZE --> PROTECTED["Protected feature or data"]', '    VERIFY -->|failure| RECOVER["Error or recovery path"]',
]
data_lines = [
    "flowchart LR", '    INPUT["User or system input"] --> VALIDATE["Validate and normalize"]',
    '    VALIDATE --> LOGIC["Application logic"]', '    LOGIC --> STORE["Persistent or local storage"]',
    '    STORE --> READ["Query / retrieval"]', '    READ --> OUTPUT["UI, API, report, or export"]',
]
deployment_lines = [
    "flowchart LR", f'    CHANGE["Change on {clean_label(branch)}"] --> CHECK["Tests and quality checks"]',
    '    CHECK --> REVIEW["Review architecture and documentation impact"]',
    '    REVIEW --> BUILD["Build or package"]', '    BUILD --> DEPLOY["Deploy or release"]',
    '    DEPLOY --> VERIFY["Verify health and rollback readiness"]',
]
contribution_lines = [
    "flowchart LR", '    FORK["Create branch"] --> CHANGE["Make focused change"]',
    '    CHANGE --> TEST["Run relevant checks"]', '    TEST --> DOCS["Update README and diagrams"]',
    '    DOCS --> PR["Open pull request"]', '    PR --> REVIEW["Review and iterate"]', '    REVIEW --> MERGE["Merge when ready"]',
]

erd_lines: list[str] = []
prisma_schema = root / "prisma" / "schema.prisma"
if prisma_schema.exists():
    schema_text = read_text(prisma_schema)
    models = re.findall(r"(?m)^model\s+(\w+)\s*\{", schema_text)[:12]
    if models:
        erd_lines = ["erDiagram"]
        for model in models:
            erd_lines.append(f"    {model} {{")
            block_match = re.search(rf"model\s+{re.escape(model)}\s*\{{(.*?)\n\}}", schema_text, re.DOTALL)
            fields = []
            if block_match:
                for line in block_match.group(1).splitlines():
                    line = line.strip()
                    if not line or line.startswith("//") or line.startswith("@@"):
                        continue
                    parts = line.split()
                    if len(parts) >= 2 and re.match(r"^[A-Za-z_]\w*$", parts[0]):
                        fields.append((parts[1].replace("?", "").replace("[]", ""), parts[0]))
                    if len(fields) >= 6:
                        break
            for field_type, field_name in fields:
                erd_lines.append(f"        {clean_label(field_type)} {clean_label(field_name)}")
            erd_lines.append("    }")

stack_text = ", ".join(frameworks[:10]) or "No primary framework detected automatically"
manifest_text = ", ".join(manifest_files[:10]) or "No standard manifest detected"
branch_url = f"https://github.com/{repository}/tree/{quote(branch, safe='/')}"
repo_url = f"https://github.com/{repository}"
issues_url = f"https://github.com/{repository}/issues"
codespace_url = f"https://github.com/codespaces/new?hide_repo_select=true&ref={quote(branch, safe='')}&repo={quote(repository, safe='')}"

badges = [static_badge(f"branch: {branch}", "5965F2")]
for item in frameworks[:6]:
    badges.append(static_badge(item, "24292F"))
if license_files:
    badges.append(static_badge("license detected", "2DA44E"))
badges.append(static_badge("docs: branch-aware", "8250DF"))

quick_start_lines = []
if package_json.exists():
    install_command = "pnpm install" if package_manager == "pnpm" else "yarn install" if package_manager == "yarn" else "npm install"
    quick_start_lines.append(install_command)
elif (root / "requirements.txt").exists():
    quick_start_lines.append("python -m venv .venv")
    quick_start_lines.append("pip install -r requirements.txt")
elif (root / "pyproject.toml").exists():
    quick_start_lines.append("python -m venv .venv")
    quick_start_lines.append("pip install -e .")
elif (root / "composer.json").exists():
    quick_start_lines.append("composer install")
elif (root / "go.mod").exists():
    quick_start_lines.append("go mod download")
elif (root / "Cargo.toml").exists():
    quick_start_lines.append("cargo build")
quick_start_lines.extend(commands[:4])

branch_scope = "This is the repository's default branch." if branch == default_branch else (
    "This branch differs from the default branch in the following detected paths:" if branch_changes else
    "No branch-specific file differences were detected against the default branch at generation time."
)
branch_change_markdown = "\n".join(f"- [`{path}`]({github_path_link(path)})" for path in branch_changes[:12])

source_table_rows = []
for area, matches in detected_areas:
    links = ", ".join(f"[`{m}`]({github_path_link(m)})" for m in matches)
    source_table_rows.append(f"| {area} | {links} |")

workflow_markdown = "\n".join(f"- [`{path}`]({github_path_link(path)})" for path in workflow_files) or "- No GitHub Actions workflow files were detected."
security_markdown = "\n".join(f"- [`{path}`]({github_path_link(path)})" for path in security_files) or "- No dedicated security policy or automated dependency configuration was detected."
observability_markdown = "\n".join(f"- [`{path}`]({github_path_link(path)})" for path in observability_files) or "- No dedicated observability integration was detected automatically."
test_markdown = "\n".join(f"- [`{path}`]({github_path_link(path)})" for path in test_paths) or "- No conventional test directory was detected automatically."
env_markdown = "\n".join(f"- `{path}`" for path in env_files) or "- No committed environment example file was detected."

conditional_sections: list[str] = []
if api_paths:
    conditional_sections.append(f'''<details open>
<summary><strong>Request lifecycle</strong></summary>

```mermaid
{chr(10).join(request_lines)}
```

Detected API or server areas: {", ".join(f"[`{p}`]({github_path_link(p)})" for p in api_paths)}.

</details>''')
if auth_files:
    conditional_sections.append(f'''<details>
<summary><strong>Authentication and authorization flow</strong></summary>

```mermaid
{chr(10).join(auth_lines)}
```

Relevant detected files: {", ".join(f"[`{p}`]({github_path_link(p)})" for p in auth_files[:10])}.

> The diagram expresses the responsibility sequence only. Confirm exact providers, token formats, roles, and recovery behavior in the linked source.

</details>''')
if data_paths or data_files:
    erd = f"\n```mermaid\n{chr(10).join(erd_lines)}\n```\n" if erd_lines else ""
    conditional_sections.append(f'''<details>
<summary><strong>Data flow and model surface</strong></summary>

```mermaid
{chr(10).join(data_lines)}
```
{erd}
Detected data areas: {", ".join(f"[`{p}`]({github_path_link(p)})" for p in (data_paths + data_files)[:12])}.

</details>''')
if job_files:
    job_nodes = ["flowchart LR", '    EVENT["Event / schedule"] --> QUEUE["Queue or job definition"]', '    QUEUE --> WORKER["Worker / processor"]', '    WORKER --> RESULT["Persist result or emit side effect"]', '    WORKER -->|failure| RETRY["Retry, alert, or dead-letter path"]']
    conditional_sections.append(f'''<details>
<summary><strong>Background jobs and scheduled work</strong></summary>

```mermaid
{chr(10).join(job_nodes)}
```

Relevant detected files: {", ".join(f"[`{p}`]({github_path_link(p)})" for p in job_files)}.

</details>''')

quick_start = ""
if quick_start_lines:
    quick_start = "```bash\n" + "\n".join(quick_start_lines) + "\n```"
else:
    quick_start = "> No reliable setup command was detected. Use the preserved project-authored notes and manifests rather than guessing."

prerequisite_text = ", ".join(prerequisites) or "Confirm from the detected manifests"

block = f'''{START}

<div align="center">

# {repo_name}

**Branch-aware technical guide for [`{branch}`]({branch_url})**

<p>{" ".join(badges)}</p>

<p>
  <a href="{branch_url}"><strong>Browse source</strong></a> ·
  <a href="{issues_url}"><strong>Issues</strong></a> ·
  <a href="{codespace_url}"><strong>Open in Codespaces</strong></a>
</p>

</div>

> [!IMPORTANT]
> This guide is generated from the files actually present on `{branch}`. It links to detected source paths, preserves project-authored notes, and avoids claiming components that were not found.

## At a glance

| Item | Detected value |
|---|---|
| Purpose | {project_description} |
| Branch role | {branch_role} |
| Stack | {stack_text} |
| Manifests | {manifest_text} |
| Prerequisites | {prerequisite_text} |
| Delivery | {", ".join(deployment_files[:10]) or "No conventional deployment configuration detected"} |
| License | {", ".join(license_files) or "No license file detected"} |

## Branch scope

{branch_scope}

{branch_change_markdown if branch_change_markdown else ""}

## Quick start

{quick_start}

### Configuration surface

{env_markdown}

> Never commit secrets, private keys, production credentials, customer data, or unredacted infrastructure details.

## Repository map

```mermaid
{chr(10).join(repo_lines)}
```

| Responsibility | Detected source paths |
|---|---|
{chr(10).join(source_table_rows)}

## Website or application map

```mermaid
{chr(10).join(route_lines)}
```

## Architecture and responsibility flow

```mermaid
{chr(10).join(architecture_lines)}
```

{chr(10).join(conditional_sections)}

## Quality, security, and operations

<table>
<tr>
<td width="33%" valign="top">

### Quality

{test_markdown}

Detected commands:
{chr(10).join(f"- `{command}`" for command in commands[:8]) or "- No standard quality command detected."}

</td>
<td width="33%" valign="top">

### Security

{security_markdown}

Review authentication, authorization, input validation, dependency updates, secret handling, and failure recovery before release.

</td>
<td width="34%" valign="top">

### Observability

{observability_markdown}

Define useful logs, metrics, traces, alerts, and rollback signals for production-facing branches.

</td>
</tr>
</table>

## Delivery flow

```mermaid
{chr(10).join(deployment_lines)}
```

### Automation detected

{workflow_markdown}

## Contribution flow

```mermaid
{chr(10).join(contribution_lines)}
```

- Keep changes focused and explain architectural consequences.
- Run the checks relevant to the changed area.
- Update diagrams whenever routes, modules, data models, authentication, jobs, or delivery paths change.
- Add screenshots or recordings for visual behavior changes when useful.
- Use issues for reproducible defects and pull requests for reviewable changes.

## Ownership and support

| Topic | Source |
|---|---|
| Repository | [`{repository}`]({repo_url}) |
| Branch | [`{branch}`]({branch_url}) |
| Ownership | {", ".join(f"[`{p}`]({github_path_link(p)})" for p in codeowner_files) or "No CODEOWNERS file detected"} |
| Contributing | {", ".join(f"[`{p}`]({github_path_link(p)})" for p in contributing_files) or "Use the contribution flow above"} |
| Support | [Open or review issues]({issues_url}) |
| License | {", ".join(f"[`{p}`]({github_path_link(p)})" for p in license_files) or "No license file detected"} |

<details>
<summary><strong>Documentation maintenance checklist</strong></summary>

- [ ] Purpose and branch scope are accurate.
- [ ] Setup and configuration commands still work.
- [ ] Repository, application, API, data, authentication, job, and deployment diagrams match the code.
- [ ] Tests, security controls, observability, and rollback behavior are documented.
- [ ] Links point to real files on this branch.
- [ ] No secrets or private operational details are exposed.

</details>

{END}'''

readme = root / "README.md"
if readme.exists():
    original = readme.read_text(encoding="utf-8", errors="replace")
else:
    original = ""

managed_pattern = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\s*", flags=re.DOTALL)
cleaned = managed_pattern.sub("", original).lstrip("\ufeff").strip()

preserved = ""
if cleaned:
    preserved = f'''\n\n<details>\n<summary><strong>Project-authored notes preserved from this branch</strong></summary>\n\n{cleaned}\n\n</details>'''

updated = block + preserved + "\n"
readme.write_text(updated, encoding="utf-8")
