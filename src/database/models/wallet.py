from pydantic import BaseModel, Field


class WalletConst(BaseModel):
    _max_transaction_amount: int = 100_000
    _min_transaction_amount: int = 100


class Wallet(WalletConst):
    """

    """
    user_id: str
    balance: int = Field(default=0, description="Balance in Cents")

    def make_payment(self, amount: int):
        if self.balance == 0:
            raise ValueError("Insufficient Balance to make payment")

        if amount < self._min_transaction_amount:
            raise ValueError(f"Payment amount must be greater than {self._min_transaction_amount}.")

        if amount > self._max_transaction_amount:
            raise ValueError(f"Payment amount must not be more than {self._max_transaction_amount}")

        if amount > self.balance:
            # Implement Rapyd payment processing here
            raise ValueError("Insufficient funds in the wallet.")
        # You can make API calls to Rapyd to process the payment
        # For example, use the Rapyd API to deduct the payment amount from the tenant's wallet
        # and add it to the property developer's wallet
        # Update the wallet balances accordingly

        # For demonstration purposes, we'll just deduct the payment amount from the balance
        self.balance -= amount

    def withdraw_funds(self, amount: int):
        if amount > self.balance:
            raise ValueError("Insufficient funds in the wallet.")
        if amount < self._min_transaction_amount:
            raise ValueError(f"Withdrawal amount must be equal to or greater than {self._min_transaction_amount}")
        if amount > self._max_transaction_amount:
            raise ValueError(
                f"Withdrawal amount must less than our Maximum Transaction Amount: {self._max_transaction_amount}")

        # Implement Rapyd withdrawal processing here
        # You can make API calls to Rapyd to initiate the withdrawal
        # For example, use the Rapyd API to transfer the withdrawal amount to the property developer's bank account

        # For demonstration purposes, we'll just deduct the withdrawal amount from the balance
        self.balance -= amount
