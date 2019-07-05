from functools import wraps
import logging
from flask import g, request
import json

from app.redis import redis
from app.models import User, AnonymousUser
from app.apiv2 import api_v2


def validate_ussd_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        """Get user trying to access to USSD session and the session id and adds them to the g request variable"""
        # get user response
        text = request.values.get("text", "default")
        text_array = text.split("*")
        # get phone number
        phone_number = request.values.get("phoneNumber")
        # get session id
        session_id = request.values.get("sessionId")
        # get user
        user = User.by_phoneNumber(phone_number) or AnonymousUser()
        # get session
        session = redis.get(session_id)
        if session is None:
            session = {"level":0,"session_id":session_id}
            redis.set(session_id, json.dumps(session))
        else:
            session = json.loads(session.decode())
        # add user, response and session to the request variable g
        g.user_response = text_array[len(text_array) - 1]
        g.session = session
        g.current_user = user
        g.phone_number = phone_number
        g.session_id = session_id
        logging.info("level {}".format(g.session.get('level')))
        return func(*args, **kwargs)
    return wrapper


@api_v2.before_app_request
@validate_ussd_user
def before_request():
    logging.info("Loading current user")