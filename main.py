import os.path
from engine.protocol import Protocol
from engine.initializer import initialize_world
from engine.plots import store_pool_stats_plot, store_pool_netflow_bars_plots
from setups.base_setup import Setup
from setups.committee_selector import AllValidatorsSelector, WeightedRandomCommitteeSelector
from setups.proposer_selector import WeightedProposerSelector
from setups.vote_policy import ProbabilisticYesVotes
from setups.reward_policy import CosmosRewardPolicy, EthereumRewardPolicy
import random

SEED = 42


# -------------------------
# COSMOS
# -------------------------
def get_cosmos_setup_non_variational(proposer_bonus_rate=0.0, online_p=0.98, vote_p=0.995):
    return Setup(
        committee_selector=AllValidatorsSelector(),  # in Cosmos : all active vote
        proposer_selector=WeightedProposerSelector(),  # proposer ~ voting_power
        vote_policy=ProbabilisticYesVotes(online_p=online_p, vote_p=vote_p),
        reward_policy=CosmosRewardPolicy(
            proposer_bonus_rate=proposer_bonus_rate,
            variational_bonus=False,
        ),
    )


def get_cosmos_setup_variational(proposer_bonus_rate=0.05, online_p=0.98, vote_p=0.995):
    return Setup(
        committee_selector=AllValidatorsSelector(),  # in Cosmos : all active vote
        proposer_selector=WeightedProposerSelector(),  # proposer ~ voting_power
        vote_policy=ProbabilisticYesVotes(online_p=online_p, vote_p=vote_p),
        reward_policy=CosmosRewardPolicy(
            proposer_bonus_rate=proposer_bonus_rate,
            variational_bonus=True,
        ),
    )


# -------------------------
# ETH + LIDO / ROCKET POOL
# -------------------------

def get_eth_lido_setup(proposer_cut=1 / 8, online_p=0.99, vote_p=0.995, scale_by_included=True):
    return Setup(
        committee_selector=AllValidatorsSelector(),
        proposer_selector=WeightedProposerSelector(),
        vote_policy=ProbabilisticYesVotes(online_p=online_p, vote_p=vote_p),
        reward_policy=EthereumRewardPolicy(proposer_cut=proposer_cut, scale_by_included=scale_by_included,
                                           execution_reward=0.0),
        pool_commission_rate=0.10
    )


def get_eth_rocketpool_setup(proposer_cut=1 / 8, online_p=0.99, vote_p=0.995, scale_by_included=True):
    return Setup(
        committee_selector=AllValidatorsSelector(),
        proposer_selector=WeightedProposerSelector(),
        vote_policy=ProbabilisticYesVotes(online_p=online_p, vote_p=vote_p),
        reward_policy=EthereumRewardPolicy(proposer_cut=proposer_cut, scale_by_included=scale_by_included,
                                           execution_reward=0.0),
        pool_commission_rate=0.14
    )


def run_simulation(com_size, number_of_rounds, reward_per_round,
                   migration_rounds_delay, rounds_per_year_count,
                   vote_omission_attack_on, vote_delay_attack_on,
                   apr_window_length, sim_setup):
    random.seed(SEED) # seed. Important for proper simulations of baseline & attacks
    world = initialize_world(
        num_validators=98,
        num_pools=9,
        num_delegators=1000,
        setup=sim_setup,
        reward_per_round=reward_per_round,
        validator_frac=0.8,
        max_validator_stake=0.33,
        aggressiveness=1.0,
        loyalty=0.0,
        pool_selection_weighted=True,
        verbose=True,
        apr_window=apr_window_length,
        pool_commission_rate=sim_setup.pool_commission_rate,
        byzantine_validator_stake=0.2,
        victim_pool_stake=0.1,
        vote_omission_attack_on=vote_omission_attack_on,
        vote_delay_attack_on=vote_delay_attack_on
    )
    protocol = Protocol(com_size, world, number_of_rounds, migration_rounds_delay, rounds_per_year_count,
                        apr_window_length)
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

    store_pool_netflow_bars_plots(history, pool_ids, folder=os.path.join(folder, "netflow"))


if __name__ == '__main__':
    committee_size = 100
    rounds = 10000
    reward = 4.26e-7
    migration_delay_rounds = 1100  # 5 days worth of epochs
    apr_window = 1575  # 7 days worth of epochs
    rounds_per_year = 82125  # 1 year worth of epochs

    setup = get_eth_lido_setup(online_p=1, vote_p=1, scale_by_included=True)
    baseline_history, baseline_world = run_simulation(committee_size, rounds, reward, migration_delay_rounds,
                                                      rounds_per_year, False, False,
                                                      apr_window, setup)


    attack_run_history, attack_world = run_simulation(committee_size, rounds, reward, migration_delay_rounds, rounds_per_year,
                                              True, False,
                                              apr_window, setup)

    # visualization
    visualize(baseline_history, baseline_world, "baseline")
    visualize(attack_run_history, attack_world, "attack")
