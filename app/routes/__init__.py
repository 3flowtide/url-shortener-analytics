def register_blueprints(app):
    from app.routes.analytics_routes import bp as analytics_bp
    from app.routes.auth_routes import bp as auth_bp
    from app.routes.link_routes import bp as links_bp
    from app.routes.redirect_routes import bp as redirect_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(links_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(redirect_bp)
