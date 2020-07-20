from __future__ import unicode_literals
from frappe import _


def get_data():
    return [
        {
            "label": _("Report"),
            "items": [
                {
                    "type": "report",
                    "name": "Custom Balance Sheet",
                    "label": "Balance Sheet"
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
