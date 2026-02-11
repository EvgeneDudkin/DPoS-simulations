from abc import ABC, abstractmethod

class RewardPolicy(ABC):
    @abstractmethod
    def distribute(self, committee, reward_amount):
        pass

class CosmosRewardPolicy(RewardPolicy):
    def __init__(self, proposer_bonus_rate=0.0, variational_bonus=False):
        self.proposer_bonus_rate = proposer_bonus_rate
        self.variational_bonus = variational_bonus

    def distribute(self, committee, reward_amount):
        max_bonus = reward_amount * self.proposer_bonus_rate
        receivers = committee.selected_voters
        total_receivers_power = sum(v.voting_power for v in receivers)
        total_committee_power = sum(v.voting_power for v in committee.validators)

        bonus = max_bonus
        if self.variational_bonus:
            frac = total_receivers_power / total_committee_power

            # normalize from [2/3..1] to [0..1]
            x = (frac - (2 / 3)) / (1 / 3)
            x = max(0.0, min(1.0, x))
            bonus = max_bonus * x

        remainder = reward_amount - bonus
        for v in receivers:
            share = remainder * (v.voting_power / total_receivers_power)
            if v == committee.proposer:
                share += bonus

            v.update_reward(share, reward_amount)

class EthereumRewardPolicy(RewardPolicy):
    def __init__(self, proposer_cut=1/8, execution_reward=0.0, scale_by_included=True):
        self.proposer_cut = proposer_cut
        self.execution_reward = execution_reward
        self.scale_by_included = scale_by_included

    def distribute(self, committee, reward_amount):
        receivers = committee.selected_voters
        included_power = sum(v.voting_power for v in receivers)
        total_power = sum(v.voting_power for v in committee.validators)

        if self.scale_by_included:
            # here we scale our reward based on the included votes
            effective_reward = reward_amount * (included_power / total_power)
        else:
            effective_reward = reward_amount

        proposer_part = effective_reward * self.proposer_cut
        attesters_part = effective_reward - proposer_part

        # proposer gets proposer_part + execution reward
        committee.proposer.update_reward(proposer_part + self.execution_reward, reward_amount)

        for v in receivers:
            share = attesters_part * (v.voting_power / included_power)
            v.update_reward(share, reward_amount)