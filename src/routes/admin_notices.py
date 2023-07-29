from datetime import datetime

from flask import Blueprint, render_template

from src.authentication import login_required
from src.database.models.notifications import NotificationsModel, Notification
from src.database.models.users import User
from src.main import notifications_controller

notices_route = Blueprint('notices', __name__)

# Create temporary data for notifications
notification1 = Notification(
    user_id="user1",
    title="New Message",
    message="You have received a new message.",
    category="message",
    time_read=None,
    is_read=False,
    time_created=datetime.now()
)

notification2 = Notification(
    user_id="user2",
    title="New Comment",
    message="Someone commented on your post.",
    category="comment",
    time_read=None,
    is_read=False,
    time_created=datetime.now()
)

notification3 = Notification(
    user_id="user1",
    title="Reminder",
    message="Don't forget your appointment tomorrow.",
    category="reminder",
    time_read=None,
    is_read=False,
    time_created=datetime.now()
)

# Create the notifications model with the temporary data
notifications_dicts: list[Notification] = [notification1, notification2, notification3]


@notices_route.get('/dashboard/notifications')
@login_required
async def get_all(user: User):
    """
    :return:
    """
    notifications_list: NotificationsModel = await notifications_controller.get_user_notifications(user_id=user.user_id)
    _notifications_dicts: list[dict[str, str]] = [notice.dict() for notice in notifications_list.all_notifications]
    if _notifications_dicts:
        _notifications_dicts = notifications_dicts

    return render_template('notifications/notifications_all.html', notifications_list=_notifications_dicts)
