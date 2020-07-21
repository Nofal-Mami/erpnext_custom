from __future__ import unicode_literals
from frappe import _


def get_data():
    return [
        {
            "label": _("Report"),
            "items": [
                {
                    "name": "Custom Balance Sheet",
                    "modules": "Custom Accounts",
                    "label": "Tunisia Balance Sheet",
                    "type": "report",
                    "is_query_report": True,
                    "doctype": 'GL Entry',
                },
            ]
        },
        {
            "label": _("Setup"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Financial Report Configuration"
                },
            ]
        },

    ]
