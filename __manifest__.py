{
    "name": "Installment Management",
    "author": "Mounir Adel",
    "description": "Installment Model",
    "depends": ["base", "account", "analytic"],
    "data": [
        "views/installment_views.xml",
        'security/group_view.xml',
        "views/installment_wizard.xml",
        "security/ir.model.access.csv",
    ],
    'installable': True,
    'application': True,
    "sequence": -100,
}
