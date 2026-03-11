from abc import ABC, abstractmethod

class RewardPolicy(ABC):
    @abstractmethod
    def distribute(self, committee, reward_amount):
        pass

class CosmosRewardPolicy(RewardPolicy):
    def __init__(self, base_reward_fraction = 0.9, proposer_bonus_fraction = 0.05, bonus_threshold = 2/3):
        self.base_reward_fraction = base_reward_fraction # a parameter from paper
        self.proposer_bonus_fraction = proposer_bonus_fraction # b parameter from paper
        self.bonus_threshold = bonus_threshold # t parameter from paper

    def distribute(self, committee, reward_amount):
        receivers = committee.selected_voters
        included_power = sum(v.voting_power for v in receivers)

        # Step 1: leader’s bonus
        leader_bonus = reward_amount * self.proposer_bonus_fraction * (1 - self.base_reward_fraction ) * ((included_power -  self.bonus_threshold) / (1 - self.bonus_threshold))
        committee.proposer.update_reward(leader_bonus)

        # Step 2: voting reward
        voting_reward = (1 - self.base_reward_fraction) * (1 - self.proposer_bonus_fraction ) * reward_amount
        for v in receivers:
            v.update_reward(voting_reward * v.voting_power)

        # Step 3: base reward
        base_reward = self.base_reward_fraction * reward_amount
        for v in committee.validators:
            v.update_reward(base_reward * v.voting_power)

        # Step 4: redistributed bonus (in case some signatures are omitted)
        redistributed_bonus = (1 - ((included_power -  self.bonus_threshold) / (1 - self.bonus_threshold))) * self.proposer_bonus_fraction * (1 - self.base_reward_fraction) * reward_amount
        for v in committee.validators:
            v.update_reward(redistributed_bonus * v.voting_power)

        # Step 4: voting reward (in case some signatures are omitted)
        voting_reward2 = (1 - included_power) * (1 - self.base_reward_fraction) * (1 - self.proposer_bonus_fraction) * reward_amount
        for v in committee.validators:
            v.update_reward(voting_reward2 * v.voting_power)

class EthereumRewardPolicy(RewardPolicy):
    def __init__(self, proposer_cut=1/8, p = 0.781):
        self.proposer_cut = proposer_cut # fraction of the leader’s bonus (parameter b from the paper)
        self.p = p # fraction of a voters reward, received on late inclusion (parameter p from the paper)

    def distribute(self, committee, reward_amount):
        # Step 1: Reward received either on timely or late inclusion.
        # Since we assume all votes are included within the window, this term is not scaled.
        base_total = reward_amount * self.p # p * R
        for v in committee.validators:
            v.update_reward(base_total * v.voting_power)

        # Step 2: The reward received only for timely inclusion and it is scaled by the included power
        receivers = committee.selected_voters
        included_power = sum(v.voting_power for v in receivers)
        timely_inclusion_reward = (1.0 - self.p) * reward_amount * included_power # (1-p) * R * ΣP

        for v in receivers:
            v.update_reward(timely_inclusion_reward * v.voting_power)

        # Step 3: The leaders bonus
        leader_bonus = self.proposer_cut *  included_power * reward_amount
        committee.proposer.update_reward(leader_bonus)