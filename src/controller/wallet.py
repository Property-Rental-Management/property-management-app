from flask import Flask

from src.controller import Controllers
from src.database.models.wallet import Wallet, WalletTransaction
from src.database.sql.wallet import WalletTransactionORM


class WalletController(Controllers):
    def __init__(self):
        super().__init__()
        self.wallets: dict[str, Wallet] = {}

    def load_and_build_wallets(self):
        wallets_by_user_id = {}
        with self.get_session() as session:
            transactions_orm_list = session.query(WalletTransactionORM).filter().all()
            transactions_list = [WalletTransaction(**transaction_orm.to_dict())
                                 for transaction_orm in transactions_orm_list]

            for transaction in transactions_list:
                # Check if the wallet already exists in the dictionary, otherwise create a new one
                if transaction.user_id not in self.wallets:
                    self.wallets[transaction.user_id] = Wallet(
                        user_id=transaction.user_id,
                        transactions=[],
                    )
                # Add the transaction to the user's wallet

                self.wallets[transaction.user_id].transactions.append(transaction)

                # Calculate the balance based on the transaction type
                if transaction.transaction_type == "deposit":
                    self.wallets[transaction.user_id].balance += transaction.amount
                elif transaction.transaction_type == "payment" or transaction.transaction_type == "withdrawal":
                    self.wallets[transaction.user_id].balance -= transaction.amount

    def init_app(self, app: Flask):
        """

        :param app:
        :return:
        """
        self.load_and_build_wallets()
