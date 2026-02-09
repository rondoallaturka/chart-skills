#!/usr/bin/env python3
"""Todoist API client wrapper using the official todoist-api-python SDK.

Provides CLI and module interfaces for managing tasks, projects, sections,
and automations (e.g., moving tasks between board columns by due date).

Requirements:
    pip install todoist-api-python

Authentication:
    export TODOIST_API_TOKEN="your_api_token_here"
    Get your token at: https://app.todoist.com/app/settings/integrations/developer
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from typing import Optional

from todoist_api_python.api import TodoistAPI


def get_client(token: Optional[str] = None) -> TodoistAPI:
    """Initialize and return a TodoistAPI client."""
    token = token or os.environ.get("TODOIST_API_TOKEN")
    if not token:
        print(
            "Error: TODOIST_API_TOKEN environment variable not set.\n"
            "Get your token at: https://app.todoist.com/app/settings/integrations/developer",
            file=sys.stderr,
        )
        sys.exit(1)
    return TodoistAPI(token)


def collect_pages(iterator) -> list:
    """Collect all pages from a paginated SDK iterator."""
    results = []
    for page in iterator:
        results.extend(page)
    return results


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

def list_projects(api: TodoistAPI) -> list[dict]:
    """List all projects with their IDs, names, and view styles."""
    projects = collect_pages(api.get_projects())
    return [
        {
            "id": p.id,
            "name": p.name,
            "color": p.color,
            "is_favorite": p.is_favorite,
            "view_style": p.view_style,
            "url": p.url,
        }
        for p in projects
    ]


def get_project(api: TodoistAPI, project_id: str) -> dict:
    """Get a single project by ID."""
    p = api.get_project(project_id)
    return {
        "id": p.id,
        "name": p.name,
        "color": p.color,
        "is_favorite": p.is_favorite,
        "view_style": p.view_style,
        "url": p.url,
    }


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def list_sections(api: TodoistAPI, project_id: Optional[str] = None) -> list[dict]:
    """List sections, optionally filtered by project."""
    sections = collect_pages(api.get_sections(project_id=project_id))
    return [
        {"id": s.id, "project_id": s.project_id, "name": s.name, "order": s.order}
        for s in sections
    ]


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def list_tasks(
    api: TodoistAPI,
    project_id: Optional[str] = None,
    section_id: Optional[str] = None,
    label: Optional[str] = None,
) -> list[dict]:
    """List active tasks with optional filters."""
    kwargs = {}
    if project_id:
        kwargs["project_id"] = project_id
    if section_id:
        kwargs["section_id"] = section_id
    if label:
        kwargs["label"] = label
    tasks = collect_pages(api.get_tasks(**kwargs))
    return [_task_to_dict(t) for t in tasks]


def filter_tasks(api: TodoistAPI, query: str) -> list[dict]:
    """Filter tasks using Todoist filter syntax (e.g., 'today', 'overdue', 'p1')."""
    tasks = collect_pages(api.filter_tasks(query=query))
    return [_task_to_dict(t) for t in tasks]


def get_task(api: TodoistAPI, task_id: str) -> dict:
    """Get a single task by ID."""
    return _task_to_dict(api.get_task(task_id))


def add_task(
    api: TodoistAPI,
    content: str,
    project_id: Optional[str] = None,
    section_id: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[int] = None,
    due_string: Optional[str] = None,
    due_date: Optional[str] = None,
    labels: Optional[list[str]] = None,
    parent_id: Optional[str] = None,
    deadline_date: Optional[str] = None,
) -> dict:
    """Create a new task."""
    kwargs = {"content": content}
    if project_id:
        kwargs["project_id"] = project_id
    if section_id:
        kwargs["section_id"] = section_id
    if description:
        kwargs["description"] = description
    if priority:
        kwargs["priority"] = priority
    if due_string:
        kwargs["due_string"] = due_string
    if due_date:
        kwargs["due_date"] = due_date
    if labels:
        kwargs["labels"] = labels
    if parent_id:
        kwargs["parent_id"] = parent_id
    if deadline_date:
        kwargs["deadline_date"] = deadline_date
    task = api.add_task(**kwargs)
    return _task_to_dict(task)


def update_task(api: TodoistAPI, task_id: str, **kwargs) -> dict:
    """Update an existing task. Pass any updatable fields as kwargs."""
    # Filter out None values
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    task = api.update_task(task_id, **kwargs)
    return _task_to_dict(task)


def complete_task(api: TodoistAPI, task_id: str) -> bool:
    """Mark a task as complete."""
    return api.complete_task(task_id)


def move_task(
    api: TodoistAPI,
    task_id: str,
    section_id: Optional[str] = None,
    project_id: Optional[str] = None,
    parent_id: Optional[str] = None,
) -> bool:
    """Move a task to a different section, project, or parent."""
    kwargs = {"task_id": task_id}
    if section_id:
        kwargs["section_id"] = section_id
    if project_id:
        kwargs["project_id"] = project_id
    if parent_id:
        kwargs["parent_id"] = parent_id
    return api.move_task(**kwargs)


def delete_task(api: TodoistAPI, task_id: str) -> bool:
    """Delete a task permanently."""
    return api.delete_task(task_id)


# ---------------------------------------------------------------------------
# Board view
# ---------------------------------------------------------------------------

def board_view(api: TodoistAPI, project_id: str) -> dict:
    """Get a board-style view of a project: tasks grouped by section."""
    sections = collect_pages(api.get_sections(project_id=project_id))
    tasks = collect_pages(api.get_tasks(project_id=project_id))

    # Group tasks by section_id
    task_map: dict[str, list[dict]] = {}
    unsectioned = []
    for t in tasks:
        td = _task_to_dict(t)
        sid = t.section_id
        if sid:
            task_map.setdefault(sid, []).append(td)
        else:
            unsectioned.append(td)

    columns = []
    if unsectioned:
        columns.append({"section": "(No section)", "section_id": None, "tasks": unsectioned})
    for s in sorted(sections, key=lambda x: x.order):
        columns.append({
            "section": s.name,
            "section_id": s.id,
            "tasks": task_map.get(s.id, []),
        })

    return {"project_id": project_id, "columns": columns}


# ---------------------------------------------------------------------------
# Day planning
# ---------------------------------------------------------------------------

def today_view(api: TodoistAPI) -> dict:
    """Get today's tasks: overdue + due today, grouped by project."""
    overdue = filter_tasks(api, "overdue")
    today = filter_tasks(api, "today")

    # Deduplicate (a task could appear in both if due today)
    seen = set()
    all_tasks = []
    for t in overdue + today:
        if t["id"] not in seen:
            seen.add(t["id"])
            all_tasks.append(t)

    # Group by project
    by_project: dict[str, list[dict]] = {}
    for t in all_tasks:
        by_project.setdefault(t["project_id"], []).append(t)

    return {"date": str(date.today()), "task_count": len(all_tasks), "by_project": by_project}


def upcoming_view(api: TodoistAPI, days: int = 7) -> list[dict]:
    """Get tasks due in the next N days."""
    end = date.today() + timedelta(days=days)
    query = f"due before: {end.isoformat()}"
    return filter_tasks(api, query)


# ---------------------------------------------------------------------------
# Automations
# ---------------------------------------------------------------------------

def auto_move_by_due_date(
    api: TodoistAPI,
    project_id: str,
    rules: list[dict],
    dry_run: bool = True,
) -> list[dict]:
    """Move tasks between sections based on due date rules.

    Each rule is a dict:
        {
            "condition": "overdue" | "today" | "upcoming" | "no_date",
            "target_section_name": "In Progress"
        }

    For "upcoming", optionally include "days": N (default 7).

    Returns a list of actions taken (or that would be taken if dry_run=True).
    """
    sections = collect_pages(api.get_sections(project_id=project_id))
    section_by_name = {s.name.lower(): s.id for s in sections}
    tasks = collect_pages(api.get_tasks(project_id=project_id))

    actions = []
    today_date = date.today()

    for task in tasks:
        due_date = _parse_due_date(task)
        matched_rule = None

        for rule in rules:
            cond = rule["condition"]
            if cond == "overdue" and due_date and due_date < today_date:
                matched_rule = rule
                break
            elif cond == "today" and due_date and due_date == today_date:
                matched_rule = rule
                break
            elif cond == "upcoming" and due_date:
                horizon = today_date + timedelta(days=rule.get("days", 7))
                if today_date < due_date <= horizon:
                    matched_rule = rule
                    break
            elif cond == "no_date" and due_date is None:
                matched_rule = rule
                break

        if matched_rule:
            target_name = matched_rule["target_section_name"].lower()
            target_id = section_by_name.get(target_name)
            if not target_id:
                continue
            # Skip if already in the target section
            if task.section_id == target_id:
                continue

            action = {
                "task_id": task.id,
                "task_content": task.content,
                "from_section_id": task.section_id,
                "to_section_id": target_id,
                "to_section_name": matched_rule["target_section_name"],
                "rule": matched_rule["condition"],
                "due": str(due_date) if due_date else None,
            }

            if not dry_run:
                api.move_task(task_id=task.id, section_id=target_id)
                action["executed"] = True
            else:
                action["executed"] = False

            actions.append(action)

    return actions


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

def list_labels(api: TodoistAPI) -> list[dict]:
    """List all personal labels."""
    labels = collect_pages(api.get_labels())
    return [
        {"id": l.id, "name": l.name, "color": l.color, "is_favorite": l.is_favorite}
        for l in labels
    ]


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

def list_comments(api: TodoistAPI, task_id: Optional[str] = None, project_id: Optional[str] = None) -> list[dict]:
    """List comments for a task or project."""
    kwargs = {}
    if task_id:
        kwargs["task_id"] = task_id
    if project_id:
        kwargs["project_id"] = project_id
    comments = collect_pages(api.get_comments(**kwargs))
    return [
        {"id": c.id, "content": c.content, "posted_at": c.posted_at, "task_id": c.task_id}
        for c in comments
    ]


def add_comment(api: TodoistAPI, content: str, task_id: Optional[str] = None, project_id: Optional[str] = None) -> dict:
    """Add a comment to a task or project."""
    kwargs = {"content": content}
    if task_id:
        kwargs["task_id"] = task_id
    if project_id:
        kwargs["project_id"] = project_id
    c = api.add_comment(**kwargs)
    return {"id": c.id, "content": c.content, "posted_at": c.posted_at}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _task_to_dict(t) -> dict:
    """Convert a Task object to a serializable dict."""
    d = {
        "id": t.id,
        "content": t.content,
        "description": t.description,
        "project_id": t.project_id,
        "section_id": t.section_id,
        "parent_id": t.parent_id,
        "labels": t.labels,
        "priority": t.priority,
        "url": t.url,
        "created_at": t.created_at,
    }
    if t.due:
        d["due"] = {
            "date": t.due.date,
            "datetime": t.due.datetime,
            "is_recurring": t.due.is_recurring,
            "string": t.due.string,
        }
    else:
        d["due"] = None
    if hasattr(t, "deadline") and t.deadline:
        d["deadline"] = {"date": t.deadline.date}
    if hasattr(t, "duration") and t.duration:
        d["duration"] = {"amount": t.duration.amount, "unit": t.duration.unit}
    return d


def _parse_due_date(task) -> Optional[date]:
    """Extract a date object from a task's due info. Returns None if no due date."""
    if not task.due:
        return None
    try:
        date_str = task.due.date
        if "T" in date_str:
            return datetime.fromisoformat(date_str).date()
        return date.fromisoformat(date_str)
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_json(data):
    print(json.dumps(data, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="Todoist CLI client")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # projects
    sub.add_parser("projects", help="List all projects")

    # sections
    sp = sub.add_parser("sections", help="List sections")
    sp.add_argument("--project-id", help="Filter by project ID")

    # tasks
    sp = sub.add_parser("tasks", help="List active tasks")
    sp.add_argument("--project-id", help="Filter by project ID")
    sp.add_argument("--section-id", help="Filter by section ID")
    sp.add_argument("--label", help="Filter by label")

    # filter
    sp = sub.add_parser("filter", help="Filter tasks using Todoist query syntax")
    sp.add_argument("query", help='Filter query (e.g., "today", "overdue", "p1")')

    # board
    sp = sub.add_parser("board", help="Board view of a project")
    sp.add_argument("project_id", help="Project ID")

    # today
    sub.add_parser("today", help="Today's tasks (overdue + due today)")

    # upcoming
    sp = sub.add_parser("upcoming", help="Tasks due in the next N days")
    sp.add_argument("--days", type=int, default=7, help="Number of days ahead (default: 7)")

    # add
    sp = sub.add_parser("add", help="Create a new task")
    sp.add_argument("content", help="Task content")
    sp.add_argument("--project-id", help="Project ID")
    sp.add_argument("--section-id", help="Section ID")
    sp.add_argument("--description", help="Task description")
    sp.add_argument("--priority", type=int, choices=[1, 2, 3, 4], help="Priority (1=normal, 4=urgent)")
    sp.add_argument("--due", help='Due string (e.g., "tomorrow", "every monday")')
    sp.add_argument("--labels", nargs="+", help="Labels to apply")

    # complete
    sp = sub.add_parser("complete", help="Complete a task")
    sp.add_argument("task_id", help="Task ID")

    # move
    sp = sub.add_parser("move", help="Move a task to a different section/project")
    sp.add_argument("task_id", help="Task ID")
    sp.add_argument("--section-id", help="Target section ID")
    sp.add_argument("--project-id", help="Target project ID")

    # auto-move
    sp = sub.add_parser("auto-move", help="Auto-move tasks between sections by due date rules")
    sp.add_argument("project_id", help="Project ID")
    sp.add_argument("--rules", required=True, help="JSON array of rules")
    sp.add_argument("--execute", action="store_true", help="Actually move (default is dry run)")

    # labels
    sub.add_parser("labels", help="List all labels")

    # comments
    sp = sub.add_parser("comments", help="List comments")
    sp.add_argument("--task-id", help="Task ID")
    sp.add_argument("--project-id", help="Project ID")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    api = get_client()

    if args.command == "projects":
        _print_json(list_projects(api))
    elif args.command == "sections":
        _print_json(list_sections(api, project_id=args.project_id))
    elif args.command == "tasks":
        _print_json(list_tasks(api, project_id=args.project_id, section_id=args.section_id, label=args.label))
    elif args.command == "filter":
        _print_json(filter_tasks(api, args.query))
    elif args.command == "board":
        _print_json(board_view(api, args.project_id))
    elif args.command == "today":
        _print_json(today_view(api))
    elif args.command == "upcoming":
        _print_json(upcoming_view(api, days=args.days))
    elif args.command == "add":
        _print_json(add_task(
            api,
            content=args.content,
            project_id=args.project_id,
            section_id=args.section_id,
            description=args.description,
            priority=args.priority,
            due_string=args.due,
            labels=args.labels,
        ))
    elif args.command == "complete":
        result = complete_task(api, args.task_id)
        print(f"Task completed: {result}")
    elif args.command == "move":
        result = move_task(api, args.task_id, section_id=args.section_id, project_id=args.project_id)
        print(f"Task moved: {result}")
    elif args.command == "auto-move":
        rules = json.loads(args.rules)
        _print_json(auto_move_by_due_date(api, args.project_id, rules, dry_run=not args.execute))
    elif args.command == "labels":
        _print_json(list_labels(api))
    elif args.command == "comments":
        _print_json(list_comments(api, task_id=args.task_id, project_id=args.project_id))


if __name__ == "__main__":
    main()
