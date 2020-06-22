{
    "name": "Office365 Base",
    "summary": "This app acts as a framework for other Office 365 apps.",
    "description": """
        Odoo 365 connector Apps
        Office 365 contacts Apps
        Office 365 connector Apps
        Office 365 contact sync
        Office 365 people sync Apps
        Office 365 people connector Apps
        Microsoft Office 365 connector
        Manual sync Apps
        Two Way Odoo Apps
        Two Way Contact sync Apps
        Contact Syncing Apps
        Two-Way Syncing Apps
        Contact Connector
        Microsoft 365 Contact Apps
        Microsoft 365 connector Apps
        Best Office 365 Apps
        Top Office 365 Apps
        Best Microsoft 365 Apps
        Best Contact Syncing Apps
        Best Connector Apps
        Best People Syncing Apps
        Office 365 Add In
        Outlook contacts sync
        Best Two Way Sync Apps
        Automatic two-way sync
        Odoo Outlook Add-In
        Two-Way Apps
        Sync Apps
        365 Apps
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
    """,
    'author': "Ksolves India Pvt. Ltd.",
    'license': 'OPL-1',
    'currency': 'EUR',
    'price': 99.0,
    'website': "https://www.ksolves.com",
    'maintainer': 'Ksolves India Pvt. Ltd.',
    'category': 'Tools',
    'version': '11.0.1.0.1',
    'support': 'sales@ksolves.com',
    "images": [
        "static/description/banners/base_banner.gif",
    ],
    "depends": ["base", "web", "auth_signup"],
    "data": [
        "views/ks_assets.xml",
        "data/ks_auth_form_data.xml",
        "views/ks_authentication.xml",
        "security/ks_office_security.xml",
        "views/ks_logs.xml",
        "views/ks_office_setting.xml",
        "views/ks_jobs.xml",
        "views/menus.xml",
        "views/ks_office365.xml",
        "views/ks_login_with_office.xml",
        "security/ir.model.access.csv",
    ],
}
