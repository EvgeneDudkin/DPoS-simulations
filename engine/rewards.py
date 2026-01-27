def distribute_committee_rewards(committee, reward_amount):
    bonus = committee.setup.bonus * reward_amount
    reward = reward_amount - bonus

    total_voters = sum(v.voting_power for v in committee.selectedVoters)
    total_committee = sum(v.voting_power for v in committee.validators)

    for validator in committee.selectedVoters:
        share = (validator.voting_power / total_voters) * reward

        if validator == committee.proposer:
            if committee.setup.variational:
                bonus_adj = ((total_voters - ((2/3)*total_committee)) / ((1/3)*total_committee)) * bonus
                share += bonus_adj
            else:
                share += bonus

        # Keep same call signature as before (even if totalReward is redundant)
        validator.update_reward(committee.validators, share, reward)
