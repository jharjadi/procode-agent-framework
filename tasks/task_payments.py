class PaymentsAgent:
    """Handles payment-related tasks (stubbed/refused)."""
    async def invoke(self, context=None):
        # Always refuse payment actions in v1
        return "Payments are not supported in this version."
