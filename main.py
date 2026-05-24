import os.path

from agents.byzantine import Byzantine
from engine.protocol import Protocol
from engine.initializer import initialize_world
from engine.plots import store_pool_stats_plot, store_pool_netflow_bars_plots
from setups.base_setup import Setup
from setups.committee_selector import AllValidatorsSelector, WeightedRandomCommitteeSelector
from setups.proposer_selector import WeightedProposerSelector
from setups.vote_policy import ProbabilisticYesVotes
from setups.reward_policy import CosmosRewardPolicy, EthereumRewardPolicy
import random
import time
SEED = 42


# -------------------------
# COSMOS
# -------------------------
def get_cosmos_setup_with_proposer_bonus(online_p=0.98, vote_p=0.995):
    return Setup(
        committee_selector=AllValidatorsSelector(),  # in Cosmos : all active vote
        proposer_selector=WeightedProposerSelector(),  # proposer ~ voting_power
        vote_policy=ProbabilisticYesVotes(online_p=online_p, vote_p=vote_p),
        reward_policy=CosmosRewardPolicy(
            base_reward_fraction=0.9,
            proposer_bonus_fraction=0.05,
            bonus_threshold=2 / 3,
        ),
    )


def get_cosmos_setup_without_proposer_bonus(proposer_bonus_rate=0.05, online_p=0.98, vote_p=0.995):
    return Setup(
        committee_selector=AllValidatorsSelector(),  # in Cosmos : all active vote
        proposer_selector=WeightedProposerSelector(),  # proposer ~ voting_power
        vote_policy=ProbabilisticYesVotes(online_p=online_p, vote_p=vote_p),
        reward_policy=CosmosRewardPolicy(
            base_reward_fraction=0.9,
            proposer_bonus_fraction=0,
            bonus_threshold=2 / 3,
        ),
    )


# -------------------------
# ETH + LIDO / ROCKET POOL
# -------------------------

def get_eth_lido_setup(online_p=0.99, vote_p=0.995):
    return Setup(
        committee_selector=AllValidatorsSelector(),
        proposer_selector=WeightedProposerSelector(),
        vote_policy=ProbabilisticYesVotes(online_p=online_p, vote_p=vote_p),
        reward_policy=EthereumRewardPolicy(),
        pool_commission_rate=0.10
    )


def get_eth_rocketpool_setup(online_p=0.99, vote_p=0.995):
    return Setup(
        committee_selector=AllValidatorsSelector(),
        proposer_selector=WeightedProposerSelector(),
        vote_policy=ProbabilisticYesVotes(online_p=online_p, vote_p=vote_p),
        reward_policy=EthereumRewardPolicy(),
        pool_commission_rate=0.14
    )


def run_simulation(com_size, number_of_rounds, reward_per_round,
                   migration_rounds_delay, rounds_per_year_count,
                   vote_omission_attack_on, vote_delay_attack_on,
                   apr_window_length, sim_setup,
                   victim_stake, attacker_stake, pool_weights,
                   loyalty, pool_selection_weighted,
                   validators_stake_dirichlet_distributed, delegators_stake_lognormal_distributed,
                   aggregators_number, pull_prob, star_gap_multiplier):
    random.seed(SEED)  # seed. Important for proper simulations of baseline & attacks
    world = initialize_world(
        num_validators=100-len(pool_weights)-2, #100 - pools - victim - attacker
        pools_voting_powers=pool_weights,
        num_delegators=1000,
        setup=sim_setup,
        reward_per_round=reward_per_round,
        validator_frac=0.8,
        max_validator_stake=0.33,
        aggressiveness=0.1,
        loyalty=loyalty,
        pool_selection_weighted=pool_selection_weighted,
        validators_stake_dirichlet_distributed=validators_stake_dirichlet_distributed,
        delegators_stake_lognormal_distributed=delegators_stake_lognormal_distributed,
        aggregators_number=aggregators_number,
        verbose=False,
        apr_window=apr_window_length,
        pool_commission_rate=sim_setup.pool_commission_rate,
        byzantine_validator_stake=attacker_stake,
        victim_pool_stake=victim_stake,
        vote_omission_attack_on=vote_omission_attack_on,
        vote_delay_attack_on=vote_delay_attack_on,
        pull_prob=pull_prob,
        star_gap_multiplier=star_gap_multiplier,
    )
    protocol = Protocol(com_size, world, number_of_rounds, migration_rounds_delay, rounds_per_year_count,
                        update_delegation_warm_up_rounds=apr_window_length * 3, verbose=False)
    protocol.run()
    return protocol.metrics.history, world


def visualize(history, world, simulation_name):
    pool_ids = [v.id for v in world.pools()]
    folder = os.path.join("out", simulation_name)
    store_pool_stats_plot(history, pool_ids, key="apr",
                          title="Pool APR over time",
                          ylabel="APR", folder=folder, filename="apr_over_time.png")

    store_pool_stats_plot(history, pool_ids, key="voting_power",
                          title="Pool market share (voting power) over time",
                          ylabel="VP share",
                          folder=folder,
                          filename="vp_share_over_time.png")

    store_pool_stats_plot(history, pool_ids, key="delegators",
                          title="Number of delegators over time",
                          ylabel="#delegators",
                          folder=folder,
                          filename="delegators_over_time.png")

    store_pool_stats_plot(history, pool_ids, key="score",
                          title="Pool reliability score (uptime) over time",
                          ylabel="score (0=never signs, 1=always signs)",
                          folder=folder,
                          filename="score_over_time.png")

    store_pool_netflow_bars_plots(history, pool_ids, folder=os.path.join(folder, "netflow"))


if __name__ == '__main__':
    committee_size = 100
    rounds = 100000
    reward = 4.26e-7
    apr_window = 1575  # 7 days worth of epochs
    rounds_per_year = 82125  # 1 year worth of epochs

    # Paper:
    # loyalty = 1
    # pool_selection_weighted = False
    # validators_stake_dirichlet_distributed = False
    # delegators_stake_lognormal_distributed = False
    #
    # pull_prob = 0.0

    # Migration included
    loyalty = 0.8
    pool_selection_weighted = True # False
    validators_stake_dirichlet_distributed = True
    delegators_stake_lognormal_distributed = True

    pull_prob = 0.03

    # cosmos setup
    setup = get_cosmos_setup_with_proposer_bonus(online_p=1, vote_p=1)
    migration_delay_rounds = 1  # immediate change
    aggregators_number = 0
    # Ethereum setup
    # setup = get_eth_lido_setup(online_p=1, vote_p=1)
    # migration_delay_rounds = 1100 # 5 days worth of epochs
    # aggregators_number = 8

    v_pow = [0.005]
    b_pow = [0.3]
    for v in v_pow:
        for b in b_pow:
            print("Victim power ", v)
            print("Attacker power ", b)
            start_time = time.time()
            baseline_history, baseline_world = run_simulation(committee_size, rounds, reward, migration_delay_rounds,
                                                              rounds_per_year, False, False,
                                                              apr_window, setup,
                                                              victim_stake=v,
                                                              attacker_stake=b,
                                                              pool_weights = [v,v,v,v],
                                                              loyalty=loyalty,
                                                              pool_selection_weighted=pool_selection_weighted,
                                                              validators_stake_dirichlet_distributed=validators_stake_dirichlet_distributed,
                                                              delegators_stake_lognormal_distributed=delegators_stake_lognormal_distributed,
                                                              aggregators_number=aggregators_number, pull_prob=pull_prob,
                                                              star_gap_multiplier=2)

            attack_run_history, attack_world = run_simulation(committee_size, rounds, reward, migration_delay_rounds,
                                                              rounds_per_year,
                                                              True, False,
                                                              apr_window, setup,
                                                              victim_stake=v,
                                                              attacker_stake=b,
                                                              pool_weights=[v,v,v,v],
                                                              loyalty=loyalty,
                                                              pool_selection_weighted=pool_selection_weighted,
                                                              validators_stake_dirichlet_distributed=validators_stake_dirichlet_distributed,
                                                              delegators_stake_lognormal_distributed=delegators_stake_lognormal_distributed,
                                                              aggregators_number=aggregators_number, pull_prob=pull_prob,
                                                              star_gap_multiplier=2)
            end_time = time.time()
            elapsed = end_time - start_time
            print(f"Elapsed Time: {elapsed:.2f} seconds")
            # visualization
            visualize(baseline_history, baseline_world, "baseline")
            visualize(attack_run_history, attack_world, "attack")

            # calculate effectiveness / cost (utility: overall_rewards)
            attr = ["overall_rewards"]
            for a in attr:
                print("Metric:", a)
                utility_baseline = {}
                delegators_baseline = {}
                attacker_utility_baseline = 0
                utility_attack = {}
                delegators_attack = {}
                attacker_utility_attack = 0
                P_attacker = 0
                for validator in baseline_world.validators:
                    if isinstance(validator, Byzantine):
                        attacker_utility_baseline = getattr(validator, a)
                        P_attacker = validator.voting_power
                        print("Attacker leader count (baseline)", validator.leader_count)
                        print("Attacker attack count (baseline)", validator.attack_count)
                    elif validator.is_pool:
                        utility_baseline[validator.id] = getattr(validator, a)
                        delegators_baseline[validator.id] = validator.dcount

                for validator in attack_world.validators:
                    if isinstance(validator, Byzantine):
                        attacker_utility_attack = getattr(validator, a)
                        P_attacker = validator.voting_power
                        print("Attacker leader count (attack)", validator.leader_count)
                        print("Attacker attack count (attack)", validator.attack_count)
                    elif validator.is_pool:
                        utility_attack[validator.id] = getattr(validator, a)
                        delegators_attack[validator.id] = validator.dcount

                eff_values = {}
                for v_id, utility_value in utility_baseline.items():
                    eff_values[v_id] = (utility_value - utility_attack[v_id]) / (utility_value * P_attacker)
                max_eff_v_id = max(eff_values, key=eff_values.get)  # id of validator for which effectiveness is max
                print("Id of validator for which effectiveness is max: ", max_eff_v_id)
                effectiveness = eff_values[max_eff_v_id]
                print("Effectiveness: ", effectiveness)

                losses = {}
                for v_id, utility_value in utility_baseline.items():
                    losses[v_id] = utility_value - utility_attack[v_id]
                loss_victim_id = max(losses, key=losses.get)  # id of validator for which loss is max
                print("Id of validator for which loss is max: ", loss_victim_id)
                attacker_loss = attacker_utility_baseline - attacker_utility_attack
                cost = attacker_loss / losses[loss_victim_id]
                print("Cost: ", cost)

                # -------------------------
                # ALLIED POOL ANALYSIS
                # -------------------------
                # Identify the pool that benefited most from the attack (captured migrating
                # delegators). Compute adjusted metrics for the hypothetical combined entity
                # (Byzantine attacker + allied pool operator = same economic actor).
                #
                # cost2 < 0  → attack was NET PROFITABLE for the combined entity
                # cost2 ∈ (0, cost) → still a net cost, but lower than cost alone
                ally_gains = {}
                for v_id, baseline_reward in utility_baseline.items():
                    extra = utility_attack[v_id] - baseline_reward
                    if extra > 0:
                        ally_gains[v_id] = extra

                if ally_gains:
                    best_ally_id = max(ally_gains, key=ally_gains.get)
                    ally_extra_reward = ally_gains[best_ally_id]
                    # VP from attack world (grew as delegators migrated to ally)
                    P_ally = next(v.voting_power for v in attack_world.validators
                                  if v.id == best_ally_id)

                    victim_loss = losses[loss_victim_id]

                    # Net cost to combined entity: negative means the attack was profitable
                    cost2 = (attacker_loss - ally_extra_reward) / victim_loss

                    print(f"Best ally pool id:          {best_ally_id}")
                    print(f"Ally extra reward:          {ally_extra_reward:.6e}")
                    print(f"Cost2 (net, attacker+ally): {cost2:.4f}")

                print("Number of Delegators (pools). Baseline:", ", ".join([f"{v_id}:{num}" for v_id, num in delegators_baseline.items()]))
                print("Number of Delegators (pools). Attack:", ", ".join([f"{v_id}:{num}" for v_id, num in delegators_attack.items()]))
