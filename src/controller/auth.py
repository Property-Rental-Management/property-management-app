import time
import uuid

from flask import Flask, render_template
from pydantic import ValidationError
from sqlalchemy import or_

from src.controller import error_handler, UnauthorizedError, Controllers
from src.database.models.profile import Profile, ProfileUpdate
from src.database.models.users import User, CreateUser, UserUpdate
from src.database.sql.user import UserORM, ProfileORM
from src.emailer import EmailModel
from src.main import send_mail


class UserController(Controllers):

    def __init__(self):
        super().__init__()
        self._time_limit = 360
        self._verification_tokens: dict[str, int | dict[str, str | int]] = {}
        self.profiles: dict[str, Profile] = {}
        self.users: dict[str, User] = {}

    def init_app(self, app: Flask):
        self._load_users()

    def _load_users(self):
        with self.get_session() as session:
            # Use session.query().options(lazyload) to fetch only the required columns
            users_orm_list: list[UserORM] = session.query(UserORM).all()
            # Convert the users_orm_list directly into a dictionary
            self.users = {user.user_id: User(**user.to_dict()) for user in users_orm_list}
            profile_orm_list: list[ProfileORM] = session.query(ProfileORM).all()
            self.profiles = {profile_orm.user_id: Profile(**profile_orm.to_dict())
                             for profile_orm in profile_orm_list}

    async def manage_users_dict(self, new_user: User):
        # Check if the user instance already exists in the dictionary
        self.users[new_user.user_id] = new_user

    async def manage_profiles(self, new_profile: Profile):
        self.profiles[new_profile.user_id] = new_profile

    @error_handler
    async def get_profile_by_user_id(self, user_id: str) -> Profile | None:
        """
        Get the profile for the given user ID.

        :param user_id: The user ID for which to retrieve the profile.
        :return: The Profile instance corresponding to the user ID if found, else None.
        """
        # Check if the profile is available in the cache (profiles dictionary)
        if user_id in self.profiles:
            self.logger.info("Fetching profile from dict {} ")
            return self.profiles.get(user_id)

        # Fetch the profile data from the database
        with self.get_session() as session:
            profile_orm = await session.query(ProfileORM).filter(ProfileORM.user_id == user_id).first()

            # If the profile_orm is not found, return None
            if not profile_orm:
                self.logger.info(f"Profile not Found")
                return {}

            # Convert ProfileORM to Profile object
            profile = Profile(user_id=profile_orm.user_id,
                              deposit_multiplier=profile_orm.deposit_multiplier,
                              currency=profile_orm.currency,
                              tax_rate=profile_orm.tax_rate)

            # Cache the profile in the dictionary for future use
            self.profiles[user_id] = profile
            self.logger.info(f"Profile ORM : {profile_orm.to_dict()}")
            self.logger.info(f"Profile : {self.profiles}")
        return profile

    @error_handler
    async def update_profile(self, user: UserUpdate, profile: ProfileUpdate):
        """

        :param user:
        :param profile:
        :return:
        """
        with self.get_session() as session:
            o_user_orm: UserORM = session.query(UserORM).filter(UserORM.user_id == user.user_id).first()
            o_profile_orm: ProfileORM = session.query(ProfileORM).filter(ProfileORM.user_id == user.user_id).first()

            if o_user_orm:
                self.logger.info(f"Updating Profile User Record : {o_user_orm}")
                o_user_orm.full_name = user.full_name
                o_user_orm.username = user.username
                o_user_orm.email = user.email
                o_user_orm.contact_number = user.contact_number
                session.merge(o_user_orm)
                self.users[user.user_id] = User(**o_user_orm.to_dict())
            # Update profile attributes

            if o_profile_orm:
                o_profile_orm.deposit_multiplier = profile.deposit_multiplier
                o_profile_orm.currency = profile.currency
                o_profile_orm.tax_rate = profile.tax_rate
                session.merge(o_profile_orm)
                self.profiles[profile.user_id] = Profile(**o_profile_orm.to_dict())
            else:
                self.logger.info(f"Adding new profile: {profile}")
                session.add(ProfileORM(**profile.dict()))
                self.profiles[profile.user_id] = Profile(**profile.dict())

            session.commit()

    async def is_token_valid(self, token: str) -> bool:
        """
        **is_token_valid**
            Checks if the password reset token is valid based on the elapsed time.
        :param token: The password reset token to validate.
        :return: True if the token is valid, False otherwise.
        """
        if token in set(self._verification_tokens.keys()):
            timestamp: int = self._verification_tokens[token]
            current_time: int = int(time.time())
            elapsed_time = current_time - timestamp
            return elapsed_time < self._time_limit

        return False

    @error_handler
    async def get(self, user_id: str) -> dict[str, str] | None:
        """
        :param user_id:
        :return:
        """
        if not user_id:
            return None
        if user_id in self.users:
            return self.users[user_id].dict()

        with self.get_session() as session:
            user_data: UserORM = session.query(UserORM).filter(UserORM.user_id == user_id).first()
            return user_data.to_dict()

    @error_handler
    async def get_by_email(self, email: str) -> User | None:
        """
            **get_by_email**
        :param email:
        :return:
        """
        if not email:
            return None
        for user in self.users.values():
            if user.email.casefold() == email.casefold():
                return user

        with self.get_session() as session:
            user_data: UserORM = session.query(UserORM).filter(UserORM.email == email.casefold()).first()

            return User(**user_data.to_dict()) if user_data else None

    @error_handler
    async def send_password_reset(self, email: str) -> dict[str, str] | None:
        """
        Sends a password reset email to the specified email address.

        :param email: The email address to send the password reset email to.
        :return: A dictionary containing the result of the email sending operation, or None if an error occurred.
        """
        # TODO please complete the method to send the password reset email
        password_reset_subject: str = "Rental-Manager.site Password Reset Request"
        # Assuming you have a function to generate the password reset link
        password_reset_link: str = self.generate_password_reset_link(email)

        html = f"""
        <html>
        <body>
            <h2>Rental-Manager.site Password Reset</h2>
            <p>Hello,</p>
            <p>We received a password reset request for your Rental Manager account. 
            Please click the link below to reset your password:</p>
            <a href="{password_reset_link}">{password_reset_link}</a>
            <p>If you didn't request a password reset, you can ignore this email.</p>
            <p>Thank you,</p>
            <p>The Rental Manager Team</p>
        </body>
        </html>
        """

        email_template = dict(to_=email, subject_=password_reset_subject, html_=html)
        await send_mail.send_mail_resend(email=EmailModel(**email_template))

        return email_template

    def generate_password_reset_link(self, email: str) -> str:
        """
        Generates a password reset link for the specified email.

        :param email: The email address for which to generate the password reset link.
        :return: The password reset link.
        """
        token = str(uuid.uuid4())  # Assuming you have a function to generate a random token
        self._verification_tokens[token] = int(time.time())
        password_reset_link = f"https://rental-manager.site/admin/reset-password?token={token}&email={email}"

        return password_reset_link

    @error_handler
    async def post(self, user: CreateUser) -> User | None:
        """

        :param user:
        :return:
        """
        with self.get_session() as session:
            user_data: UserORM = session.query(UserORM).filter(or_(UserORM.user_id == user.user_id,
                                                                   UserORM.email == user.email)).first()
            if user_data:
                return None

            new_user: UserORM = UserORM(**user.to_dict())
            session.add(new_user)
            new_user_dict = new_user.to_dict()
            session.commit()
            _user_data = User(**new_user_dict) if isinstance(new_user, UserORM) else None
            self.users[_user_data.user_id] = _user_data
            return _user_data

    @error_handler
    async def put(self, user: User) -> dict[str, str] | None:
        with self.get_session() as session:
            user_data: UserORM = session.query(UserORM).filter_by(user_id=user.user_id).first()
            if not user_data:
                return None

            # Update user_data with the values from the user Pydantic BaseModel
            for field in user_data.__table__.columns.keys():
                if hasattr(user, field):
                    setattr(user_data, field, getattr(user, field))

            # Save the updated user_data back to the session
            session.add(user_data)
            session.commit()
            self.users[user_data.user_id] = user_data
            return user_data.to_dict()

    @error_handler
    async def login(self, username: str, password: str) -> User | None:
        with self.get_session() as session:
            user_data: UserORM = session.query(UserORM).filter_by(username=username).first()
            try:
                if user_data:
                    user: User = User(**user_data.to_dict())
                else:
                    return None
            except ValidationError as e:
                raise UnauthorizedError(description="Cannot Login User please check your login details")

            return user if user.is_login(password=password) else None

    @error_handler
    async def send_verification_email(self, user: User) -> None:
        """
        Sends a verification email to the specified user.

        :param user: The user to send the verification email to.
        """
        print(f"user passed on : {user}")
        token = str(uuid.uuid4())  # Assuming you have a function to generate a verification token
        verification_link = f"https://rental-manager.site/admin/verify-email?token={token}&email={user.email}"
        self._verification_tokens[token] = dict(email=user.email, timestamp=int(time.time()))
        # Render the email template
        email_html = render_template("email_templates/verification_email.html", user=user,
                                     verification_link=verification_link)

        msg = EmailModel(subject_="Rental-Manager.site Email Verification",
                         to_=user.email,
                         html_=email_html)

        await send_mail.send_mail_resend(email=msg)

    @error_handler
    async def verify_email(self, email: str, token: str) -> bool:
        """
            **verify_email**
        :param email:
        :param token:
        :return:
        """
        if email is None:
            return False
        if token is None:
            return False
        if token not in self._verification_tokens:
            return False

        _data: dict[str, str | int] = self._verification_tokens[token]

        current_time: int = int(time.time())
        elapsed_time = current_time - int(_data.get('timestamp', 0))
        return (elapsed_time < self._time_limit) and (email.casefold() == _data.get('email'))
