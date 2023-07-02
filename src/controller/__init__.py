import functools
from flask import redirect, url_for, flash

from src.logger import init_logger
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError

error_logger = init_logger("error_logger")


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
            error_logger.error(str(e))
            flash(message="Error accessing database - please try again", category='danger')
            return None
        except UnauthorizedError as e:
            error_logger.error(str(e))
            flash(message="You are not authorized to access this resource", category='danger')
            return redirect(url_for('home.get_home'), code=302)
        except ConnectionResetError as e:
            error_logger.error(str(e))
            flash(message="Ooh , took a nap, sorry lets do that again...", category='danger')
            return None
        except Exception as e:
            _error = str(e)
            error_logger.error(f" {view_func.__name__} : {_error}")
            flash(message="Ooh , some things broke, no worries, please continue...", category='danger')
            return None

    return wrapped_method
