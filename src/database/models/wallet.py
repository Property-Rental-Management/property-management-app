from datetime import datetime

from pydantic import BaseModel, Field, PositiveInt


class TransactionType(str):
    deposit = "deposit"
    payment = "payment"
    withdrawal = "withdrawal"


class WalletTransaction(BaseModel):
    """
    Transaction model represents an individual transaction.
    """
    date: datetime = Field(default_factory=datetime.utcnow)
    transaction_type: str
    destination_wallet: str
    amount: PositiveInt


class WalletConst(BaseModel):
    _max_transaction_amount: PositiveInt = 100_000
    _min_transaction_amount: PositiveInt = 100


class Wallet(WalletConst):
    """
    Wallet class represents a user's wallet with balance and transaction operations.
    """
    user_id: str
    balance: int = Field(default=0, description="Balance in Cents")
    transactions: list[WalletTransaction] = Field(default=[], description="List of transaction details")

    def make_payment(self, amount: PositiveInt, destination_wallet: str):
        if self.balance == 0:
            raise ValueError("Insufficient Balance to make payment")

        if amount < self._min_transaction_amount:
            raise ValueError(f"Payment amount must be greater than {self._min_transaction_amount}.")

        if amount > self._max_transaction_amount:
            raise ValueError(f"Payment amount must not be more than {self._max_transaction_amount}")

        if amount > self.balance:
            raise ValueError("Insufficient funds in the wallet.")

        # Implement payment processing here
        # You can make API calls to process the payment with a payment gateway

        # For demonstration purposes, we'll just deduct the payment amount from the balance
        self.balance -= amount
        self._record_transaction(amount, TransactionType.payment, destination_wallet)

    def withdraw_funds(self, amount: PositiveInt):
        if amount > self.balance:
            raise ValueError("Insufficient funds in the wallet.")
        if amount < self._min_transaction_amount:
            raise ValueError(f"Withdrawal amount must be equal to or greater than {self._min_transaction_amount}")
        if amount > self._max_transaction_amount:
            raise ValueError(f"Withdrawal amount must be less than our Maximum "
                             f"Transaction Amount: {self._max_transaction_amount}")

        # Implement withdrawal processing here
        # You can make API calls to initiate the withdrawal

        # For demonstration purposes, we'll just deduct the withdrawal amount from the balance
        self.balance -= amount
        self._record_transaction(amount, TransactionType.withdrawal, self.user_id)

    def deposit_funds(self, amount: PositiveInt):
        if amount < self._min_transaction_amount:
            raise ValueError(f"Deposit amount must be equal to or greater than {self._min_transaction_amount}")
        if amount > self._max_transaction_amount:
            raise ValueError(f"Deposit amount must be less than our Maximum "
                             f"Transaction Amount: {self._max_transaction_amount}")

        # Implement deposit processing here
        # You can make API calls to process the deposit with a payment gateway

        # For demonstration purposes, we'll just add the deposit amount to the balance
        self.balance += amount
        self._record_transaction(amount=amount, transaction_type=TransactionType.deposit)

    def _record_transaction(self, amount: PositiveInt, transaction_type: str, other_wallet: str):
        transaction = WalletTransaction(
            amount=amount,
            transaction_type=transaction_type,
            destination_wallet=other_wallet,
        )
        self.transactions.append(transaction)

    def get_transactions(self, limit: int | None = None) -> list[WalletTransaction]:
        """
        Get the list of transactions.

        Args:
            limit (Optional[int]): Maximum number of transactions to retrieve. Defaults to None (retrieve all).

        Returns:
            List[Transaction]: List of transaction details.
        """
        if limit is None:
            return self.transactions
        else:
            return self.transactions[-limit:]

    def get_transaction_count(self) -> int:
        """
        Get the total number of transactions.

        Returns:
            int: Total number of transactions.
        """
        return len(self.transactions)
