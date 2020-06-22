{
    "name": "Office365 Calendar",
    "summary": """
        This app allows you to sync Office 365 Calendar events with Odoo calendar events and vice-versa.
    """,
    "description": """
        365 Apps
        Odoo Office 365 Apps
        Office 365 Apps
        Odoo 365 connector Apps
        Office 365 Calendar Apps
        Office 365 connector Apps
        Office 365 Calendar sync
        Office 365 Outlook sync Apps
        Office 365 Outlook connector Apps
        Microsoft Office 365 Calendar
        Manual sync Apps
        Two-Way Odoo Apps
        Two-Way Calendar sync Apps
        Calendar Syncing Apps
        Two-Way Syncing Apps
        Calendar Connector
        Microsoft 365 Calendar Apps
        Microsoft 365 connector Apps
        Best Office 365 Apps
        Top Office 365 Apps
        Best Microsoft 365 Apps
        Best Calendar Syncing Apps
        Best Connector Apps
        Best Outlook Syncing Apps
        Office 365 Add In
        Outlook Calendar sync
        Best Two-Way Sync Apps
        Automatic two-way sync
        Odoo Outlook Add-In
        Sync Outlook to Odoo
        Two-Way Apps
    """,
    'author': "Ksolves India Pvt. Ltd.",
    'license': 'OPL-1',
    'currency': 'EUR',
    'price': 100.0,
    'website': "https://www.ksolves.com",
    'maintainer': 'Ksolves India Pvt. Ltd.',
    'category': 'Tools',
    'version': '11.0.1.1.3',
    'support': 'sales@ksolves.com',
    "depends": ["base", "ks_office365_base", "calendar"],
    "images": [
        "static/description/banners/calendar_banner.gif",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/ks_calendar.xml",
        "views/ks_assets.xml",
        "data/ks_calendar_cron.xml",
    ],
}
