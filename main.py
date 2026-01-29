from agents.byzantine import Byzantine
from agents.validator import Validator
from engine.protocol import Protocol
from agents.delegator import Delegator
from setups.randomselect import RandomSelect
from engine.world import World
import matplotlib.pyplot as plt
from engine.initializer import initialize_world

if __name__ == '__main__':
    committee_size = 20
    rounds = 50000
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

    rewards = [v.total_reward for v in world.validators]

    dcounts = [v.dcount / rounds for v in world.validators]

    overall_rewards = [v.overall_rewards for v in world.validators]

    print(dcounts)
    print(rewards)
    print(overall_rewards)

    # Generate x-axis values
    x = range(len(rewards))

    # Create the bar plot
    plt.bar(x, rewards)

    # Add labels and title
    plt.xlabel('Item')
    plt.ylabel('Reward')
    plt.title('Comparison of Rewards')

    # Display the plot
    plt.show()

    plt.bar(x, dcounts)

    # Add labels and title
    plt.xlabel('Validators')
    plt.ylabel('Average number of delegators per round')
    plt.title('Comparison')

    # Display the plot
    plt.show()
