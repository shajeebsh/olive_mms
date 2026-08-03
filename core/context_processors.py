"""Data-driven module registry for the top navigation ribbon.

Only add/edit navigation here — never hardcode the ribbon in templates.
Modules are shown when their app is installed and their index URL resolves.
Later, ``institution.MosqueProfile.enabled_modules`` will further filter this.
"""

from django.urls import NoReverseMatch, reverse


MODULE_REGISTRY = [
    {"key": "core", "label": "Dashboard", "icon": "bi-speedometer2", "url_name": "core:index"},
    {"key": "institution", "label": "Institution", "icon": "bi-buildings", "url_name": "institution:index"},
    {"key": "members", "label": "Members", "icon": "bi-people", "url_name": "members:index"},
    {"key": "donations", "label": "Donations", "icon": "bi-heart", "url_name": "donations:index"},
    {"key": "finance", "label": "Finance", "icon": "bi-cash-stack", "url_name": "finance:index"},
    {"key": "madrassa", "label": "Madrassa", "icon": "bi-mortarboard", "url_name": "madrassa:index"},
    {"key": "events", "label": "Events", "icon": "bi-calendar-event", "url_name": "events:index"},
    {"key": "inventory", "label": "Inventory", "icon": "bi-box-seam", "url_name": "inventory:index"},
    {"key": "reporting", "label": "Reports", "icon": "bi-graph-up", "url_name": "reporting:index"},
]


def navigation_menu(request):
    """Build the module ribbon from installed, URL-resolvable modules."""
    modules = []
    for module in MODULE_REGISTRY:
        try:
            reverse(module["url_name"])
        except NoReverseMatch:
            continue
        modules.append({**module, "url": reverse(module["url_name"])})
    return {"modules": modules}
