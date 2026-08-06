import json
import os
import re
from collections import Counter
from pathlib import Path
from urllib.parse import quote

START = "<!-- interactive-readme-standard:start -->"
END = "<!-- interactive-readme-standard:end -->"

repository = os.environ["REPOSITORY"]
branch = os.environ["BRANCH_NAME"]
repo_name = repository.split("/", 1)[1]
root = Path(".")

IGNORED = {
    ".git",
    ".next",
    ".nuxt",
    ".output",
    ".venv",
    "venv",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "target",
    "__pycache__",
    ".cache",
}


def clean_label(value: str) -> str:
    return value.replace('"', "'").replace("[", "(").replace("]", ")")


def display_path(path: Path) -> str:
    return f"{path.name}/" if path.is_dir() else path.name


entries = sorted(
    [p for p in root.iterdir() if p.name not in IGNORED and p.name != "README.md"],
    key=lambda p: (not p.is_dir(), p.name.lower()),
)

frameworks: list[str] = []
commands: list[str] = []
manifest_files: list[str] = []


def add_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


package_json = root / "package.json"
if package_json.exists():
    manifest_files.append("package.json")
    try:
        package = json.loads(package_json.read_text(encoding="utf-8"))
        dependencies = {}
        dependencies.update(package.get("dependencies") or {})
        dependencies.update(package.get("devDependencies") or {})
        scripts = package.get("scripts") or {}
        framework_map = {
            "next": "Next.js",
            "react": "React",
            "vue": "Vue",
            "nuxt": "Nuxt",
            "svelte": "Svelte",
            "@sveltejs/kit": "SvelteKit",
            "astro": "Astro",
            "vite": "Vite",
            "express": "Express",
            "fastify": "Fastify",
            "@nestjs/core": "NestJS",
            "electron": "Electron",
            "tailwindcss": "Tailwind CSS",
            "typescript": "TypeScript",
        }
        for dependency, label in framework_map.items():
            if dependency in dependencies:
                add_unique(frameworks, label)
        for script_name in (
            "dev",
            "start",
            "build",
            "test",
            "lint",
            "typecheck",
            "preview",
        ):
            if script_name in scripts:
                add_unique(commands, f"npm run {script_name}")
    except (OSError, ValueError, TypeError):
        pass

manifest_map = {
    "pyproject.toml": ["Python"],
    "requirements.txt": ["Python"],
    "Pipfile": ["Python"],
    "poetry.lock": ["Poetry"],
    "pom.xml": ["Java", "Maven"],
    "build.gradle": ["Java", "Gradle"],
    "build.gradle.kts": ["Kotlin", "Gradle"],
    "go.mod": ["Go"],
    "Cargo.toml": ["Rust", "Cargo"],
    "composer.json": ["PHP", "Composer"],
    "Gemfile": ["Ruby"],
    "pubspec.yaml": ["Dart", "Flutter"],
    "Dockerfile": ["Docker"],
    "docker-compose.yml": ["Docker Compose"],
    "compose.yaml": ["Docker Compose"],
}
for manifest, labels in manifest_map.items():
    if (root / manifest).exists():
        manifest_files.append(manifest)
        for label in labels:
            add_unique(frameworks, label)

if (root / "manage.py").exists():
    add_unique(frameworks, "Python")
    add_unique(frameworks, "Django")
    add_unique(commands, "python manage.py runserver")
    add_unique(commands, "python manage.py test")

if (root / "artisan").exists():
    add_unique(frameworks, "Laravel")

if (root / "wp-content").exists() or (
    (root / "style.css").exists() and (root / "functions.php").exists()
):
    add_unique(frameworks, "WordPress")

extension_labels = {
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".py": "Python",
    ".java": "Java",
    ".kt": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".rb": "Ruby",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".swift": "Swift",
    ".dart": "Dart",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "Sass",
    ".vue": "Vue",
    ".svelte": "Svelte",
}
counts: Counter[str] = Counter()
scanned = 0
for current_root, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in IGNORED]
    relative_depth = len(Path(current_root).relative_to(root).parts)
    if relative_depth > 4:
        dirs[:] = []
        continue
    for filename in files:
        scanned += 1
        if scanned > 8000:
            break
        label = extension_labels.get(Path(filename).suffix.lower())
        if label:
            counts[label] += 1
    if scanned > 8000:
        break

for language, _ in counts.most_common(6):
    add_unique(frameworks, language)

route_candidates: list[str] = []
for candidate in (
    "app",
    "pages",
    "routes",
    "site",
    "web",
    "frontend",
    "src/app",
    "src/pages",
    "src/routes",
    "src/screens",
    "src/views",
    "templates",
    "public",
):
    if (root / candidate).exists():
        route_candidates.append(candidate)

route_files: list[str] = []
for base in route_candidates[:6]:
    base_path = root / base
    if not base_path.is_dir():
        continue
    for path in sorted(base_path.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if len(relative.parts) > 4:
            continue
        if path.suffix.lower() in {
            ".html",
            ".htm",
            ".jsx",
            ".tsx",
            ".vue",
            ".svelte",
            ".astro",
            ".php",
            ".py",
        }:
            route_files.append(str(relative))
        if len(route_files) >= 14:
            break
    if len(route_files) >= 14:
        break

area_candidates = {
    "Interface": [
        "app",
        "pages",
        "site",
        "web",
        "frontend",
        "client",
        "public",
        "templates",
        "components",
        "src",
    ],
    "Application logic": [
        "server",
        "backend",
        "api",
        "services",
        "service",
        "lib",
        "core",
        "domain",
    ],
    "Data": ["db", "database", "models", "migrations", "prisma", "data", "storage"],
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
    fallback = [display_path(p) for p in entries[:5]] or ["README.md"]
    detected_areas.append(("Project files", fallback))

deployment_files = [
    name
    for name in (
        "Dockerfile",
        "docker-compose.yml",
        "compose.yaml",
        "netlify.toml",
        "vercel.json",
        "render.yaml",
        "fly.toml",
        "Procfile",
        "firebase.json",
        "wrangler.toml",
    )
    if (root / name).exists()
]
if (root / ".github" / "workflows").exists():
    deployment_files.append("GitHub Actions")

shown_entries = entries[:18]
remaining_entries = max(0, len(entries) - len(shown_entries))
repo_lines = [
    "flowchart TD",
    f'    ROOT["{clean_label(repo_name)} / {clean_label(branch)}"]',
]
for index, path in enumerate(shown_entries):
    repo_lines.append(
        f'    ROOT --> P{index}["{clean_label(display_path(path))}"]'
    )
if remaining_entries:
    repo_lines.append(
        f'    ROOT --> MORE["+ {remaining_entries} more top-level entries"]'
    )

architecture_lines = ["flowchart LR", '    ACTOR["User / contributor"]']
previous = "ACTOR"
for index, (area, matches) in enumerate(detected_areas):
    node = f"A{index}"
    detail = ", ".join(matches)
    architecture_lines.append(
        f'    {previous} --> {node}["{clean_label(area)}: {clean_label(detail)}"]'
    )
    previous = node
if deployment_files:
    architecture_lines.append(
        f'    {previous} --> DELIVERY["Delivery: {clean_label(", ".join(deployment_files[:5]))}"]'
    )

route_lines = ["flowchart TD", f'    APP["{clean_label(repo_name)}"]']
if route_candidates:
    for index, candidate in enumerate(route_candidates[:8]):
        route_lines.append(f'    APP --> R{index}["{clean_label(candidate)}"]')
    for index, route_file in enumerate(route_files[:12]):
        parent_index = 0
        for candidate_index, candidate in enumerate(route_candidates[:8]):
            if route_file == candidate or route_file.startswith(candidate.rstrip("/") + "/"):
                parent_index = candidate_index
                break
        route_lines.append(
            f'    R{parent_index} --> F{index}["{clean_label(route_file)}"]'
        )
else:
    route_lines.extend(
        [
            '    APP --> SOURCE["No conventional route directory detected"]',
            '    SOURCE --> VERIFY["Inspect the project-specific documentation below"]',
        ]
    )

check_labels = commands[:5]
if not check_labels:
    for candidate in (
        "Makefile",
        "package.json",
        "pyproject.toml",
        "pom.xml",
        "build.gradle",
        "Cargo.toml",
        "go.mod",
    ):
        if (root / candidate).exists():
            check_labels.append(f"Checks defined by {candidate}")
if not check_labels:
    check_labels.append("Project-specific validation")

delivery_lines = [
    "flowchart LR",
    f'    CHANGE["Change on {clean_label(branch)}"]',
    f'    CHECK["Validate: {clean_label(", ".join(check_labels))}"]',
    '    REVIEW["Review documentation and architecture impact"]',
    '    RELEASE["Merge, release, or deploy according to this branch"]',
    "    CHANGE --> CHECK --> REVIEW --> RELEASE",
]

stack_text = ", ".join(frameworks[:10]) or "No primary framework detected automatically"
manifest_text = ", ".join(manifest_files[:10]) or "No standard manifest detected"
branch_url = f"https://github.com/{repository}/tree/{quote(branch, safe='/')}"

block = f'''{START}

> [!NOTE]
> **Branch-specific documentation:** this section is maintained for [`{branch}`]({branch_url}). It is generated from the files present on this branch and preserves the project-authored README below.

<details open>
<summary><strong>Interactive repository guide</strong></summary>

## Branch overview

| Item | Value |
|---|---|
| Repository | [`{repository}`](https://github.com/{repository}) |
| Branch | [`{branch}`]({branch_url}) |
| Detected stack | {stack_text} |
| Detected manifests | {manifest_text} |
| Documentation policy | Every maintained branch must explain purpose, setup, structure, architecture, flows, testing, delivery, security, and ownership. |

## Repository structure

```mermaid
{chr(10).join(repo_lines)}
```

The diagram is generated from the branch's actual top-level files and directories. Use the branch link above for complete source navigation.

## Website or application structure

```mermaid
{chr(10).join(route_lines)}
```

## Application and responsibility flow

```mermaid
{chr(10).join(architecture_lines)}
```

## Change-to-delivery flow

```mermaid
{chr(10).join(delivery_lines)}
```

## README requirements for this branch

- Explain what this branch contains and how it differs from the default branch.
- Keep installation, configuration, usage, testing, deployment, security, support, and license information accurate.
- Document repository, website or application, API, data, authentication, background-job, and deployment flows when they exist.
- Prefer Mermaid diagrams and expandable `<details>` sections for visual navigation.
- Link diagrams and modules to real source paths; never invent missing components.
- Preserve project-specific documentation and update diagrams whenever architecture or major paths change.
- Treat secrets, private infrastructure, customer data, and credentials as prohibited README content.

</details>

{END}'''

readme = root / "README.md"
if readme.exists():
    original = readme.read_text(encoding="utf-8", errors="replace")
else:
    original = f"# {repo_name}\n\nProject documentation for the `{branch}` branch.\n"

managed_pattern = re.compile(
    re.escape(START) + r".*?" + re.escape(END) + r"\s*",
    flags=re.DOTALL,
)
cleaned = managed_pattern.sub("", original).lstrip("\ufeff")
heading_match = re.search(r"^#\s+.+$", cleaned, flags=re.MULTILINE)
if heading_match:
    insertion = heading_match.end()
    updated = (
        cleaned[:insertion].rstrip()
        + "\n\n"
        + block
        + "\n\n"
        + cleaned[insertion:].lstrip()
    )
else:
    updated = f"# {repo_name}\n\n{block}\n\n{cleaned.lstrip()}"

readme.write_text(updated.rstrip() + "\n", encoding="utf-8")
