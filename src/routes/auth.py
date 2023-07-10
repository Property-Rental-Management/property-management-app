from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, make_response, flash, redirect, url_for, Response
from pydantic import ValidationError

from src.database.models.auth import Auth, RegisterUser
from src.database.models.users import User, CreateUser, PasswordResetUser
from src.logger import init_logger
from src.main import user_controller

auth_route = Blueprint('auth', __name__)
auth_logger = init_logger('auth_logger')

REMEMBER_ME_DELAY = 60 * 60 * 24 * 30


async def create_response(redirect_url, message=None, category=None) -> Response:
    response = make_response(redirect(redirect_url))
    if message and category:
        flash(message=message, category=category)
    return response


@auth_route.get('/admin/login')
async def get_login():
    """
    **get_login**
        get login
    :return:
    """
    # TODO - CHECK IF USER IS ALREADY LOGGED IN
    return render_template('login.html')


@auth_route.post('/admin/login')
async def do_login():
    try:
        auth_user = Auth(**request.form)
    except ValidationError as e:
        auth_logger.error(str(e))
        return await create_response(url_for('auth.get_login'), 'Login failed. Check your username and password.',
                                     'danger')

    login_user: User | None = await user_controller.login(username=auth_user.username, password=auth_user.password)
    if login_user and login_user.username == auth_user.username:
        response = await create_response(url_for('companies.get_companies'))

        # Setting Loging Cookie
        delay = REMEMBER_ME_DELAY if auth_user.remember == "on" else 30
        expiration = datetime.utcnow() + timedelta(minutes=delay)
        response.set_cookie('auth', value=login_user.user_id, expires=expiration, httponly=True)

        if not login_user.account_verified:
            _ = await user_controller.send_verification_email(user=login_user)
            flash(message="A verification email has been sent please verify your email", category="danger")
        return response
    else:
        return await create_response(url_for('auth.get_login'),
                                     'Login failed. you may not be registered in this system', 'danger')


@auth_route.get('/admin/logout')
async def do_logout():
    """

    :return:
    """
    # TODO - CHECK IF USER IS ALREADY LOGGED IN
    response = await create_response(url_for('home.get_home'))
    response.delete_cookie('auth')
    flash(message='You have been successfully logged out.', category='danger')
    return response


@auth_route.get('/admin/register')
async def get_register():
    """

    :return:
    """
    # TODO - CHECK IF USER IS ALREADY LOGGED IN
    return render_template('register.html')


@auth_route.post('/admin/register')
async def do_register():
    """
        **do_register**

    :return:
    """
    # TODO - CHECK IF USER IS ALREADY LOGGED IN
    try:
        register_user: RegisterUser = RegisterUser(**request.form)
    except ValidationError as e:
        auth_logger.error(str(e))
        return await create_response(url_for('auth.get_register'), 'Please fill in all the required fields.', 'danger')

    user_exist: User | None = await user_controller.get_by_email(email=register_user.email)
    # user bool test for the conditions necessary to validate the user
    if user_exist:
        flash(message='User Already Exist please login', category='success')
        return await create_response(url_for('auth.get_login'))
    print(f"registering user : {register_user}")
    user_data: CreateUser = CreateUser(**register_user.dict(exclude={'terms'}))

    _user_data: User | None = await user_controller.post(user=user_data)
    if _user_data:
        flash(message='Successfully logged in', category='success')
        response: Response = await create_response(url_for('companies.get_companies'))
        expiration = datetime.utcnow() + timedelta(minutes=30)
        response.set_cookie('auth', value=user_data.user_id, expires=expiration, httponly=True)
        return response

    flash(message='failed to create new user try again later', category='danger')
    return await create_response(url_for('home.get_home'))


@auth_route.get('/admin/password-reset')
async def get_password_reset():
    """
        **get_password_reset**
    :return:
    """
    return render_template('password_reset.html')


@auth_route.post('/admin/password-reset')
async def do_password_reset():
    email = request.form.get('email')
    if not email:
        flash(message='Please submit an email in order to proceed with password reset', category='danger')
        return await create_response(url_for('auth.get_password_reset'))

    email_exist = await user_controller.get_by_email(email=email)
    if email_exist is not None:
        flash(message='Password reset email sent to your Inbox', category='success')
        await user_controller.send_password_reset(email=email)
    else:
        flash(message='That Email was not found on our system please create a new account', category='success')

    return await create_response(url_for('home.get_home'))


@auth_route.route('/admin/reset-password', methods=['GET', 'POST'])
async def reset_password():
    """
    **reset_password**
    Resets the password for the user associated with the provided token.


    :return: A response indicating the result of the password reset operation.
    """
    if request.method == "GET":
        token = request.args.get('token')
        email = request.args.get('email')
        if token and email and user_controller.is_token_valid(token=token):
            return render_template("do_reset_password.html", email=email)

    elif request.method == "POST":
        password = request.form.get('password')
        email = request.form.get('email')
        if not password or not email:
            flash(message="Invalid request. Please provide both email and password.", category="danger")
            return redirect(url_for('home.get_home'))
        # TODO - refactor this can do better
        old_user = await user_controller.get_by_email(email=email)

        if not old_user:
            flash(message="Invalid email. Please try again.", category="danger")
            return redirect(url_for('home.get_home'))

        old_user_dict = old_user.dict(exclude={'password_hash'})
        old_user_dict['password'] = password
        new_user = PasswordResetUser(**old_user_dict)
        updated_user = await user_controller.put(user=new_user)
        if not updated_user:
            flash(message="Failed to update password. Please try again.", category="danger")
            return redirect(url_for('home.get_home'))

        flash(message="Successfully updated password. Please login.", category="success")
        return redirect(url_for('home.get_home'))

    flash(message="Invalid request. Please try again.", category="danger")
    return redirect(url_for('home.get_home'), code=302)


@auth_route.get('/admin/verify-email')
async def verify_email():
    """
        **verify_email**
        :return:
    """

    token = request.args.get('token')
    email = request.args.get('email')
    email_verified: bool = await user_controller.verify_email(email=email, token=token)
    if email_verified:
        user: User = await user_controller.get_by_email(email=email)
        user.account_verified = True
        _update_user = await user_controller.put(user=user)
        if _update_user and _update_user.get('account_verified', False):
            flash(message="Account Verified successfully", category="success")
        else:
            flash(message="Your Account could not be verified, please log out", category="danger")
        return redirect(url_for('home.get_home'), code=302)
    flash(message="Unable to verify your email please try again later", category="danger")
    return redirect(url_for('home.get_home'), code=302)
