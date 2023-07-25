import functools

from flask import redirect, url_for, flash
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError

from src.database.sql import Session
from src.logger import init_logger

error_logger = init_logger("error_logger")


class Controllers:

    def __init__(self, session_maker=Session):
        self.sessions = [session_maker() for _ in range(20)]
        self.logger = init_logger(self.__class__.__name__)

    def get_session(self) -> Session:
        if self.sessions:
            return self.sessions.pop()
        self.sessions = [Session() for _ in range(20)]
        return self.get_session()


class UnauthorizedError(Exception):
    def __init__(self, description: str = "You are not Authorized to access that resource", code: int = 401):
        self.description = description
        self.code = code
        super().__init__(self.description)


def error_handler(view_func):
    @functools.wraps(view_func)
    async def wrapped_method(*args, **kwargs):
        try:
            return await view_func(*args, **kwargs)
        except (OperationalError, ProgrammingError, IntegrityError, AttributeError) as e:
            message: str = f"{view_func.__name__} : {str(e)}"
            error_logger.error(message)
            flash(message="Error accessing database - please try again", category='danger')
            return None
        except UnauthorizedError as e:
            message: str = f"{view_func.__name__} : {str(e)}"
            error_logger.error(message)
            flash(message="You are not authorized to access this resource", category='danger')
            return redirect(url_for('home.get_home'), code=302)
        except ConnectionResetError as e:
            message: str = f"{view_func.__name__} : {str(e)}"
            error_logger.error(message)
            flash(message="Unable to connect to database please retry", category='danger')
            return None

        except ValidationError as e:
            message: str = f"{view_func.__name__} : {str(e)}"
            error_logger.error(message)
            return None

        except Exception as e:
            message: str = f"{view_func.__name__} : {str(e)}"
            error_logger.error(message)
            flash(message="Ooh , some things broke, no worries, please continue...", category='danger')
            return None

    return wrapped_method
