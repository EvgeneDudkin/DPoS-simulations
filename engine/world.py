class World:
    def __init__(self, validators, delegators, setup, reward):
        self.validators = validators
        self.delegators = delegators
        self.setup = setup
        self.reward = reward

        self.blockchain = []
        self.round_index = 0

    def pools(self):
        """Validators that are eligible to receive delegations."""
        return [v for v in self.validators if v.is_pool]
