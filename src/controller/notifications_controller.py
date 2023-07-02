from src.controller import error_handler
from src.database.models.notifications import NotificationsModel, Notification
from src.database.sql.notifications import NotificationORM
from src.database.sql import Session


class NotificationsController:

    def __init__(self):
        pass

    @staticmethod
    @error_handler
    async def get_user_notifications(user_id: str) -> NotificationsModel | None:
        """

        :param user_id:
        :return:
        """
        with Session() as session:
            notifications: list[NotificationORM] = session.query(NotificationORM).filter(
                NotificationORM.user_id == user_id).all()
            notifications_ = [Notification(**notification.dict()) for notification in notifications]
            if notifications_:
                notifications_list: NotificationsModel = NotificationsModel(**dict(notifications=notifications_))
                return notifications_list
            return None
