# import random
# from setups.base_setup import Setup
#
# class Cosmos(Setup):
#
#     def __init__(self):
#         super().__init__()
#         self.bonus = 0.05
#
#     def select_validators(self, pool, size):
#         sorted_pool = sorted(pool, key=lambda x: x.voting_power, reverse=True)
#         return sorted_pool[:size]