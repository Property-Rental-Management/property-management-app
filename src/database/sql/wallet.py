from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, inspect

from src.database.constants import ID_LEN
from src.database.sql import engine, Base


class WalletTransactionORM(Base):
    __tablename__ = 'wallet_transactions'
    transaction_id: str = Column(String(ID_LEN), primary_key=True)
    user_id: str = Column(String(ID_LEN), nullable=False)
    date: datetime = Column(DateTime)
    transaction_type: str = Column(String(16), nullable=False)
    pay_to_wallet: str = Column(String(ID_LEN), nullable=False)
    payment_from_wallet: str = Column(String(ID_LEN), nullable=False)
    amount: int = Column(Integer, nullable=False)

    @classmethod
    def create_if_not_table(cls):
        if not inspect(engine).has_table(cls.__tablename__):
            Base.metadata.create_all(bind=engine)

    def to_dict(self) -> dict:
        """
        Convert the WalletTransaction object to a dictionary representation.

        Returns:
            dict: Dictionary containing the attributes of the WalletTransaction.
        """
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "date": self.date,
            "transaction_type": self.transaction_type,
            "pay_to_wallet": self.pay_to_wallet,
            "payment_from_wallet": self.payment_from_wallet,
            "amount": self.amount,
        }

    def __eq__(self, other):
        """
        Override the equality dunder method to compare WalletTransaction instances based on transaction_id and user_id.

        Args:
            other (WalletTransaction): The other instance to compare with.

        Returns:
            bool: True if the two instances have the same transaction_id and user_id, False otherwise.
        """
        if not isinstance(other, WalletTransactionORM):
            return False
        return (self.transaction_id == other.transaction_id) and (self.user_id == other.user_id)
