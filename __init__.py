"""Étape 1 — Création de l'application ANSARTECH 224."""

import click
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_login import current_user, logout_user

from config import Config

from .extensions import csrf, db, login_manager
from .models import utcnow


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .tenancy import init_tenancy
    init_tenancy()

    from .routes.analytics import bp as analytics_bp
    from .routes.archives import bp as archives_bp
    from .routes.auth import bp as auth_bp
    from .routes.dashboard import bp as dashboard_bp
    from .routes.products import bp as products_bp
    from .routes.purchases import bp as purchases_bp
    from .routes.sales import bp as sales_bp
    from .routes.settings import bp as settings_bp
    from .routes.platform import bp as platform_bp
    from .routes.stock import bp as stock_bp

    for blueprint in (auth_bp, dashboard_bp, products_bp, stock_bp, purchases_bp,
                      sales_bp, analytics_bp, archives_bp, settings_bp, platform_bp):
        app.register_blueprint(blueprint)

    _register_template_helpers(app)
    _register_security(app)
    _register_errors(app)
    _register_commands(app)

    with app.app_context():
        from .seed import init_database
        init_database(app)
        # Ferme les connexions ouvertes avant que gunicorn ne crée ses workers
        db.engine.dispose()

    return app


def _register_template_helpers(app):
    from .models import Message, Product
    from .utils import all_settings, current_company, money, number

    app.jinja_env.filters["money"] = money
    app.jinja_env.filters["num"] = number
    app.jinja_env.filters["date"] = lambda d: d.strftime("%d/%m/%Y") if d else ""
    app.jinja_env.filters["datetime"] = lambda d: d.strftime("%d/%m/%Y %H:%M") if d else ""

    def form_lines(form):
        """Reconstitue les lignes produit d'un formulaire renvoyé avec erreurs."""
        if not hasattr(form, "getlist"):
            return []
        from .extensions import db as _db
        from .utils import to_float, to_int
        lines = []
        ids, qtys, prices = form.getlist("product_id[]"), form.getlist("quantity[]"), form.getlist("price[]")
        for i, raw in enumerate(ids):
            product = _db.session.get(Product, to_int(raw) or 0)
            if product:
                lines.append({"id": product.id, "sku": product.sku, "name": product.name,
                              "stock": product.quantity, "unit": product.unit,
                              "qty": to_float(qtys[i] if i < len(qtys) else 1, 1),
                              "price": to_float(prices[i] if i < len(prices) else 0, 0)})
        return lines

    app.jinja_env.globals["form_lines"] = form_lines

    @app.context_processor
    def inject_globals():
        data = {"app_name": app.config["APP_NAME"], "now": utcnow(), "in_platform": False,
                "company": None, "support_mode": False}
        if current_user.is_authenticated:
            settings = all_settings()
            data["settings"] = settings
            data["company"] = current_company()
            data["in_platform"] = data["company"] is None
            data["support_mode"] = current_user.role == "superadmin" and data["company"] is not None
            if data["in_platform"]:
                data["unread_count"] = 0
                data["low_stock_count"] = 0
                return data
            data["unread_count"] = Message.query.filter(
                Message.recipient_id == current_user.id,
                Message.is_read.is_(False),
            ).count()
            data["low_stock_count"] = Product.query.filter(
                Product.is_active.is_(True), Product.quantity <= Product.min_stock
            ).count() if settings.get("low_stock_alert") == "1" else 0
        return data


def _register_security(app):
    @app.before_request
    def set_tenant():
        """Détermine l'entreprise active pour toute la requête."""
        g.company_id = None
        if request.endpoint == "static" or not current_user.is_authenticated:
            return None
        if current_user.role == "superadmin":
            if request.blueprint != "platform":
                g.company_id = session.get("support_company_id")
            if g.company_id is None and request.blueprint not in ("platform", "auth") \
                    and request.endpoint is not None:
                return redirect(url_for("platform.index"))
            return None
        company = current_user.company
        if company is None or not company.can_login:
            reason = "expiré" if company is not None and company.is_expired else "suspendu"
            logout_user()
            flash(f"L'abonnement de votre entreprise est {reason}. Contactez ANSARTECH 224.", "danger")
            return redirect(url_for("auth.login"))
        g.company_id = company.id
        return None

    @app.before_request
    def force_password_change():
        if (current_user.is_authenticated and current_user.must_change_password
                and request.endpoint not in ("auth.change_password", "auth.logout", "static")):
            return redirect(url_for("auth.change_password"))

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        if current_user.is_authenticated and response.mimetype == "text/html":
            response.headers["Cache-Control"] = "no-store"
        return response


def _register_errors(app):
    from flask_wtf.csrf import CSRFError

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errors/error.html", code=403,
                               message="Vous n'avez pas les droits pour accéder à cette page."), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/error.html", code=404, message="Page introuvable."), 404

    @app.errorhandler(413)
    def too_large(_e):
        return render_template("errors/error.html", code=413,
                               message="Fichier trop volumineux (5 Mo maximum)."), 413

    @app.errorhandler(CSRFError)
    def csrf_error(_e):
        return render_template("errors/error.html", code=400,
                               message="Session expirée. Rechargez la page et réessayez."), 400

    @app.errorhandler(500)
    def server_error(_e):
        db.session.rollback()
        return render_template("errors/error.html", code=500,
                               message="Erreur interne. L'opération n'a pas été enregistrée."), 500


def _register_commands(app):
    @app.cli.command("init-db")
    def init_db_command():
        """Crée les tables et le compte administrateur."""
        from .seed import init_database
        init_database(app)
        click.echo("Base de données prête.")

    @app.cli.command("demo-data")
    def demo_data_command():
        """Crée une entreprise de démonstration avec des données d'exemple."""
        from .seed import create_demo_company
        create_demo_company()
        click.echo("Données de démonstration ajoutées.")

    @app.cli.command("reset-admin")
    @click.argument("password")
    def reset_admin(password):
        """Réinitialise le mot de passe du super-administrateur de la plateforme."""
        from .models import User
        user = User.query.filter_by(role="superadmin").order_by(User.id).first()
        if not user:
            click.echo("Administrateur introuvable.")
            return
        user.set_password(password)
        user.failed_attempts = 0
        user.locked_until = None
        user.is_active_account = True
        db.session.commit()
        click.echo("Mot de passe administrateur réinitialisé.")
