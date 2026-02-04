from agents.byzantine import Byzantine
from agents.validator import Validator
from engine.protocol import Protocol
from agents.delegator import Delegator
from setups.randomselect import RandomSelect
from engine.world import World
import matplotlib.pyplot as plt
from engine.initializer import initialize_world
from engine.plots import store_pool_stats_plot, store_pool_netflow_bars_plots

if __name__ == '__main__':
    committee_size = 100
    rounds = 100000
    reward = 4.26e-7
    migration_delay_rounds = 1100 # 5 days worth of epochs
    apr_window = 1575  # 7 days worth of epochs
    rounds_per_year = 82125 # 1 year worth of epochs

    #setup = Cosmos()
    setup = RandomSelect()
    world = initialize_world(
        num_validators=100,
        num_pools=10,
        num_delegators=1000,
        setup=setup,
        reward_per_round=reward,
        validator_frac=0.8,
        max_validator_stake=0.33,
        aggressiveness=1,
        loyalty=0.0,
        pool_selection_weighted=True,
        verbose=True,
        apr_window=apr_window
    )
    protocol = Protocol(committee_size, world, rounds, migration_delay_rounds, rounds_per_year, apr_window)
    protocol.run()

    # visualization
    history = protocol.metrics.history
    pool_ids = [v.id for v in world.pools()]
    # APR
    store_pool_stats_plot(history, pool_ids, key="apr",
                    title="Pool APR over time",
                    ylabel="APR", filename="apr_over_time.png")

    store_pool_stats_plot(history, pool_ids, key="vp_share",
                    title="Pool market share (voting power share) over time",
                    ylabel="VP share",
                    filename="vp_share_over_time.png")

    store_pool_stats_plot(history, pool_ids, key="delegators",
                    title="Number of delegators over time",
                    ylabel="#delegators",
                    filename="delegators_over_time.png")

    store_pool_netflow_bars_plots(history, pool_ids)