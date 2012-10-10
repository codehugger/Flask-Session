# -*- coding: utf-8 -*-
"""
    flaskext.session
    ~~~~~~~~~~~~~~~~

    Adds basic server-side session support to your application.
    This module is based on Armin Ronacher's server session code.

    :copyright: (c) 2012 by Bjarki Gudlaugsson (codehugger).
    :license: BSD, see LICENSE for more details.
"""
import pickle
from datetime import timedelta
from uuid import uuid4
from redis import Redis
from werkzeug.datastructures import CallbackDict
from flask.sessions import SessionInterface, SessionMixin


class Session(object):
    """
    Manages server session storage

    :param app: Flask instance
    """

    def __init__(self, app=None):

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initializes your session settings from the application
        settings.

        You can use this if you want to set up your Session instance
        at configuration time.

        :param app: Flask application instance
        """
        self.server = app.config.get('SESSION_SERVER', '127.0.0.1')
        self.password = app.config.get('SESSION_PASSWORD')
        self.port = app.config.get('SESSION_PORT', 6379)
        self.db = app.config.get('SESSION_REDIS_DB', 0)
        self.debug = int(app.config.get('SESSION_DEBUG', app.debug))

        r = Redis(
            host=self.server,
            port=self.port,
            password=self.password,
            db=self.db)

        app.session_interface = RedisSessionInterface(r)

        # register extensions with app
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['session'] = self


class RedisSession(CallbackDict, SessionMixin):

    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class RedisSessionInterface(SessionInterface):
    serializer = pickle
    session_class = RedisSession

    def __init__(self, redis=None, prefix='session:'):
        if redis is None:
            redis = Redis()
        self.redis = redis
        self.prefix = prefix

    def generate_sid(self):
        return str(uuid4())

    def get_redis_expiration_time(self, app, session):
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid)
        val = self.redis.get(self.prefix + sid)
        if val is not None:
            data = self.serializer.loads(val)
            return self.session_class(data, sid=sid)
        return self.session_class(sid=sid, new=True)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        if not session:
            self.redis.delete(self.prefix + session.sid)
            if session.modified:
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain)
            return
        redis_exp = self.get_redis_expiration_time(app, session)
        cookie_exp = self.get_expiration_time(app, session)
        val = self.serializer.dumps(dict(session))
        self.redis.setex(self.prefix + session.sid,
                         val,
                         int(redis_exp.days * 24 * 60 * 60 +
                             redis_exp.seconds +
                             redis_exp.microseconds / 100000))
        response.set_cookie(app.session_cookie_name, session.sid,
                            expires=cookie_exp, httponly=True,
                            domain=domain)
