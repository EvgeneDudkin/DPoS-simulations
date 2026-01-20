from agents.byzantine import Byzantine
from agents.validator import Validator
from engine.protocol import Protocol
from agents.delegator import Delegator
from setups.randomselect import RandomSelect
import matplotlib.pyplot as plt

if __name__ == '__main__':
    validators = []
    delegators = []
    for i in range(70):
        validators.append(Validator(len(validators), 200))
    for i in range(30):
        validators.append(Byzantine(len(validators), 200, [validators[0]], False))
    for i in range(1000):
        delegators.append(Delegator(len(delegators), 50, 1, 0))

    committeeSize = 20
    rounds = 500
    reward = 1000

    #setup = Cosmos()
    setup = RandomSelect()

    protocol = Protocol(committeeSize, validators, delegators, rounds, setup, reward)
    protocol.run()

    rewards = [v.totalReward for v in validators]

    dcounts = [v.dcount/rounds for v in validators]

    overallrewards = [v.overallRewards for v in validators]

    print(dcounts)
    print(rewards)
    print(overallrewards)

    # Generate x-axis values (0 to 99 in this case)
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