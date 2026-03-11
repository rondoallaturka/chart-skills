---
name: todoist
description: Manage Todoist tasks, projects, and boards — plan your day and automate workflows
version: 1.0.0
author: chart-skills
tags: [todoist, tasks, productivity, boards, kanban, automation, planning]
---

# Todoist

Manage your Todoist tasks, projects, and boards directly from Claude. Plan your day, review your board, create and move tasks, and set up automations like moving tasks between sections when due dates hit.

## Usage

```
/todoist <what you want to do>
```

### Examples

```
/todoist show me my board
/todoist what's on my plate today?
/todoist add a task "Review PR #42" to the In Progress column due tomorrow
/todoist move overdue tasks to the Urgent section
/todoist plan my week — show upcoming tasks and help me prioritize
/todoist when tasks become overdue, auto-move them to "Needs Attention"
```

## Setup

### 1. Install the SDK

```bash
pip install todoist-api-python
```

### 2. Set your API token

Get your token at: https://app.todoist.com/app/settings/integrations/developer

```bash
export TODOIST_API_TOKEN="your_token_here"
```

### 3. Helper script

The reusable helper is at `scripts/todoist_client.py`. It wraps the official SDK and provides both a Python module API and a CLI.

## Instructions

When the user invokes this skill, follow the workflow below. Always start by confirming you can connect, then fulfill their request.

### Step 1: Connect and orient

Before doing anything, verify the token works and understand the user's workspace.

```python
from todoist_api_python.api import TodoistAPI
import os

api = TodoistAPI(os.environ["TODOIST_API_TOKEN"])

# List projects to orient
projects = []
for page in api.get_projects():
    projects.extend(page)
for p in projects:
    print(f"{p.id}: {p.name} ({p.view_style})")
```

If the user mentions a specific board or project (e.g., "Main Board"), find it by name. The project's `view_style` will be `"board"` for kanban boards or `"list"` for list views.

### Step 2: Understand the board structure

For board/kanban projects, sections represent columns. Always fetch sections to understand the layout.

```python
sections = []
for page in api.get_sections(project_id=PROJECT_ID):
    sections.extend(page)
for s in sections:
    print(f"  [{s.id}] {s.name} (order: {s.order})")
```

### Step 3: Fulfill the user's request

Match the request to the right operation:

#### Viewing tasks

| Request | Approach |
|---------|----------|
| "Show my board" | Use `board_view()` from the helper script, or fetch tasks grouped by section |
| "What's due today?" | Use `filter_tasks(query="today")` or the `today` filter |
| "Show overdue tasks" | Use `filter_tasks(query="overdue")` |
| "What's coming up this week?" | Use `filter_tasks(query="7 days")` |
| "Show tasks in section X" | Use `get_tasks(section_id=SECTION_ID)` |
| "Search for tasks about X" | Use `filter_tasks(query="search: X")` |

**Todoist filter syntax reference** (pass to `filter_tasks`):
- `today` — due today
- `overdue` — past due
- `7 days` or `next 7 days` — due within 7 days
- `no date` — tasks without a due date
- `p1` / `p2` / `p3` / `p4` — by priority (p1 = urgent)
- `@label_name` — by label
- `#Project Name` — by project
- `/Section Name` — by section
- `assigned to: me` — assigned to you
- `search: keyword` — full-text search
- Combine with `&` (and) or `|` (or): `today & p1`

#### Creating tasks

```python
task = api.add_task(
    content="Review PR #42",
    project_id=PROJECT_ID,
    section_id=SECTION_ID,         # place in specific board column
    description="Check the auth changes",
    priority=3,                     # 1=normal, 2=medium, 3=high, 4=urgent
    due_string="tomorrow",          # natural language: "every monday", "Jan 15", "in 3 days"
    labels=["work", "code-review"],
    deadline_date="2026-02-14",     # hard deadline (separate from due date)
)
print(f"Created: {task.content} (ID: {task.id})")
```

**Quick Add** — parses natural language like the Todoist quick-add bar:
```python
task = api.add_task_quick(text="Review PR #42 tomorrow p2 @work #Main Board")
```

#### Moving tasks

Moving a task to a different board column (section):
```python
api.move_task(task_id=TASK_ID, section_id=TARGET_SECTION_ID)
```

Moving to a different project:
```python
api.move_task(task_id=TASK_ID, project_id=TARGET_PROJECT_ID)
```

#### Updating tasks

```python
api.update_task(
    task_id=TASK_ID,
    content="Updated title",
    due_string="next friday",
    priority=4,
    labels=["urgent", "work"],
)
```

#### Completing tasks

```python
api.complete_task(task_id=TASK_ID)
```

#### Comments

```python
# Add a note to a task
api.add_comment(content="Blocked on design review", task_id=TASK_ID)

# Read comments
for page in api.get_comments(task_id=TASK_ID):
    for c in page:
        print(f"  {c.posted_at}: {c.content}")
```

### Step 4: Automations

The user's key use case is automating task movement based on conditions. Use the helper script's `auto_move_by_due_date` or build custom logic.

#### Auto-move by due date (helper script)

```python
from scripts.todoist_client import get_client, auto_move_by_due_date

api = get_client()

rules = [
    {"condition": "overdue", "target_section_name": "Urgent"},
    {"condition": "today", "target_section_name": "In Progress"},
    {"condition": "upcoming", "target_section_name": "Up Next", "days": 3},
    {"condition": "no_date", "target_section_name": "Backlog"},
]

# Dry run first — shows what WOULD move
actions = auto_move_by_due_date(api, PROJECT_ID, rules, dry_run=True)
for a in actions:
    print(f"  Would move '{a['task_content']}' → {a['to_section_name']} (rule: {a['rule']})")

# Execute for real
actions = auto_move_by_due_date(api, PROJECT_ID, rules, dry_run=False)
```

#### CLI usage for auto-move

```bash
python scripts/todoist_client.py auto-move PROJECT_ID \
  --rules '[{"condition": "overdue", "target_section_name": "Urgent"}, {"condition": "today", "target_section_name": "In Progress"}]' \
  --execute
```

#### Custom automation logic

For more complex rules (e.g., move based on labels, priority, or arbitrary conditions):

```python
api = TodoistAPI(os.environ["TODOIST_API_TOKEN"])

tasks = []
for page in api.get_tasks(project_id=PROJECT_ID):
    tasks.extend(page)

sections = []
for page in api.get_sections(project_id=PROJECT_ID):
    sections.extend(page)
section_by_name = {s.name.lower(): s.id for s in sections}

for task in tasks:
    # Example: move high-priority tasks without a due date to "Needs Triage"
    if task.priority >= 3 and not task.due:
        target = section_by_name.get("needs triage")
        if target and task.section_id != target:
            api.move_task(task_id=task.id, section_id=target)
            print(f"Moved '{task.content}' → Needs Triage")
```

### Step 5: Day planning workflow

When the user wants help planning their day:

1. **Show today's load**: Fetch overdue + due today tasks
2. **Show the board state**: Board view grouped by section
3. **Identify priorities**: Sort by priority, flag overdue items
4. **Suggest rebalancing**: If too many tasks are due today, suggest rescheduling some
5. **Create missing tasks**: If the user mentions things not yet tracked, add them

```python
# Today's overview
overdue = []
for page in api.filter_tasks(query="overdue"):
    overdue.extend(page)

today = []
for page in api.filter_tasks(query="today"):
    today.extend(page)

print(f"Overdue: {len(overdue)} tasks")
print(f"Due today: {len(today)} tasks")

for t in sorted(overdue + today, key=lambda x: x.priority, reverse=True):
    flag = "OVERDUE" if t in overdue else "today"
    print(f"  [{flag}] p{t.priority} {t.content}")
```

## CLI Reference

The helper script at `scripts/todoist_client.py` provides these subcommands:

| Command | Description |
|---------|-------------|
| `projects` | List all projects |
| `sections --project-id ID` | List sections in a project |
| `tasks --project-id ID --section-id ID --label NAME` | List tasks with filters |
| `filter "query"` | Filter tasks using Todoist syntax |
| `board PROJECT_ID` | Board view (tasks grouped by section) |
| `today` | Today's tasks (overdue + due today) |
| `upcoming --days N` | Tasks due in the next N days |
| `add "content" --project-id ID --section-id ID --due "tomorrow"` | Create a task |
| `complete TASK_ID` | Mark a task complete |
| `move TASK_ID --section-id ID` | Move a task to a section |
| `auto-move PROJECT_ID --rules JSON --execute` | Auto-move tasks by due date rules |
| `labels` | List all labels |
| `comments --task-id ID` | List comments on a task |

## Common Pitfalls

1. **Token not set** — The most common error. Ensure `TODOIST_API_TOKEN` is exported in your shell environment.
2. **Project ID vs name** — The API uses string IDs, not names. Always list projects first to find the ID.
3. **Section ID for board columns** — Board columns are sections. Use `get_sections(project_id=...)` to map column names to IDs.
4. **Priority is inverted** — In the API, `priority=4` is the most urgent (p1 in the UI), `priority=1` is normal (p4 in the UI).
5. **Pagination** — SDK methods return iterators of pages. Always iterate with `for page in result: for item in page:` or use the helper's `collect_pages()`.
6. **Due string vs due date** — `due_string` accepts natural language ("tomorrow", "every monday"). `due_date` accepts ISO format ("2026-02-15"). Use one or the other, not both.
7. **Filters are powerful** — Before writing custom code, check if a Todoist filter expression can do what you need. The filter syntax supports complex logic.
8. **Rate limits** — The API has rate limits. For bulk operations, add small delays between requests if processing many tasks.
