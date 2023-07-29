import os

from flask import Flask

from src.emailer import SendMail
from src.utils import (template_folder, static_folder, format_with_grouping, lease_formatter, format_square_meters,
                       format_payment_method)

send_mail = SendMail()

from src.controller.auth import UserController
from src.controller.companies import CompaniesController
from src.controller.encryptor import encryptor
from src.controller.notifications_controller import NotificationsController
from src.controller.lease_controller import LeaseController
from src.controller.tenant import TenantController
from src.controller.lease_controller import InvoiceManager
from src.controller.wallet import WalletController
from src.firewall import Firewall

firewall = Firewall()

tenant_controller = TenantController()
company_controller = CompaniesController()
user_controller = UserController()
notifications_controller = NotificationsController()
lease_agreement_controller = LeaseController()
wallet_controller = WalletController()

cache_path = os.path.join(os.getcwd(), "cache", "invoices_cache.pkl")
invoice_man = InvoiceManager(cache_path)


def _add_blue_prints(app):
    """
        this function adds blueprints
    :param app:
    :return:
    """
    from src.routes.home import home_route
    from src.routes.companies import companies_route
    from src.routes.buildings import buildings_route
    from src.routes.maintenance import maintenance_route
    from src.routes.reports import reports_route
    from src.routes.payments import payments_route
    from src.routes.invoices import invoices_route
    from src.routes.statements import statements_route
    from src.routes.tenants import tenants_route
    from src.routes.admin_notices import notices_route
    from src.cron.routes import cron_route
    from src.routes.auth import auth_route
    from src.routes.admin.admin import admin_routes

    app.register_blueprint(home_route)
    app.register_blueprint(companies_route)
    app.register_blueprint(buildings_route)
    app.register_blueprint(maintenance_route)
    app.register_blueprint(reports_route)
    app.register_blueprint(payments_route)
    app.register_blueprint(invoices_route)
    app.register_blueprint(statements_route)
    app.register_blueprint(auth_route)
    app.register_blueprint(tenants_route)
    app.register_blueprint(cron_route)
    app.register_blueprint(notices_route)
    app.register_blueprint(admin_routes)


def _add_filters(app):
    """
        **add_filters**
            filters allows formatting from models to user readable format
    :param app:
    :return:
    """
    app.jinja_env.filters['currency'] = format_with_grouping
    app.jinja_env.filters['lease_counter'] = lease_formatter
    app.jinja_env.filters['square_meters'] = format_square_meters
    app.jinja_env.filters['payment_method'] = format_payment_method


def create_app(config):
    app: Flask = Flask(__name__)

    app.template_folder = template_folder()
    app.static_folder = static_folder()
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['BASE_URL'] = "https://rental-manager.site"

    with app.app_context():
        from src.main.bootstrapping import bootstrapper
        bootstrapper()

        encryptor.init_app(app=app)
        user_controller.init_app(app=app)
        tenant_controller.init_app(app=app)
        company_controller.init_app(app=app)
        lease_agreement_controller.init_app(app=app)
        wallet_controller.init_app(app=app)

        firewall.init_app(app=app)
        send_mail.init_app(app=app)
        invoice_man.init_app(app=app)

        _add_blue_prints(app)
        _add_filters(app)

    return app
