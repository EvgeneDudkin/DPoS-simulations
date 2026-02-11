import random
from engine.world import World  # adjust import if your World lives elsewhere
from agents.validator import Validator
from agents.delegator import Delegator


# We use a Dirichlet-style distribution (via Gamma draws + normalization)
# to generate validator self-stake shares.
#
# This ensures:
# - all stakes are positive,
# - the total stake is conserved,
#
# Dirichlet distributions are standard for modeling market shares,
# stake distributions, and resource allocation under uncertainty.
def _random_positive_vector(n, alpha=1.0):
    # Gamma draws -> Dirichlet-like when normalized
    xs = [random.gammavariate(alpha, 1.0) for _ in range(n)]
    s = sum(xs)
    return [x / s for x in xs]


def _get_shares(total, n, max_stake, min_stake=0.001, alpha=1.0, max_iter=10_000):
    """
    Returns n nonnegative shares that sum to `total` and each <= cap.
    Simple rejection + fallback redistribution.
    """
    if min_stake > max_stake:
        raise ValueError("min_stake cannot exceed max_stake")

    if n * min_stake > total + 1e-12:
        raise ValueError(f"Impossible: n*min_stake={n * min_stake:.6f} > total={total:.6f}")

    if n * max_stake < total - 1e-12:
        raise ValueError(f"Impossible: n*max_stake={n * max_stake:.6f} < total={total:.6f}")

    remaining = total - n * min_stake
    cap_remaining = max_stake - min_stake

    # Rejection sampling is fine for thesis-scale n.
    for _ in range(max_iter):
        shares_unit = _random_positive_vector(n, alpha=alpha)
        shares = [remaining * x for x in shares_unit]
        if max(shares) <= cap_remaining  + 1e-12:
            return [min_stake + r for r in shares]

    # Fallback: max_stake then renormalize remaining mass iteratively
    shares = [remaining  * x for x in _random_positive_vector(n, alpha=alpha)]
    for _ in range(n * 5):
        over = [i for i, s in enumerate(shares) if s > cap_remaining]
        if not over:
            break
        excess = sum(shares[i] - cap_remaining for i in over)
        for i in over:
            shares[i] = cap_remaining
        under = [i for i, s in enumerate(shares) if s < cap_remaining - 1e-15]
        if not under:
            break
        under_room = [cap_remaining - shares[i] for i in under]
        room_sum = sum(under_room)
        if room_sum <= 0:
            break
        for i, room in zip(under, under_room):
            shares[i] += excess * (room / room_sum)

    # final normalization to correct tiny numerical drift
    s = sum(shares)
    if s > 0:
        shares = [x * (remaining / s) for x in shares]
    # ensure max_stake (numerical)
    shares = [min_stake + x for x in shares]
    return shares

# Delegator stakes are sampled from a lognormal distribution
# and then normalized to the target total.
#
# Lognormal distributions are commonly used to model wealth
# and capital allocation, capturing the presence of many small
# holders and a small number of large stakeholders ("whales").
#
# This heterogeneity is important for realistic migration
# and attack-amplification dynamics.
def _lognormal_stakes(total, n, mu=-2.0, sigma=1.0):
    xs = [random.lognormvariate(mu, sigma) for _ in range(n)]
    s = sum(xs)
    return [total * (x / s) for x in xs]

def initialize_world(
        *,
        num_validators: int,
        num_pools: int,
        num_delegators: int,
        setup,
        reward_per_round: float,
        validator_frac: float = 0.8,
        max_validator_stake: float = 0.33,
        delegator_mu: float = -2.0,
        delegator_sigma: float = 1.0,
        aggressiveness: float = 1.0,
        loyalty: float = 0.0,
        pool_selection_weighted: bool = True,
        verbose: bool = False,
        apr_window: int = 1000,
        pool_commission_rate: float = 0.0,
):
    """
    Creates validators + delegators with normalized total stake = 1.0.
    - validators get self-bonded stake summing to validator_frac
    - each validator self-stake <= max_validator_stake
    - delegators get stake summing to 1 - validator_frac
    - delegators are initially assigned to pool validators (is_pool=True)
    """
    if not (0.0 < validator_frac < 1.0):
        raise ValueError("validator_frac must be between 0 and 1 (exclusive).")
    if num_pools > num_validators:
        raise ValueError("num_pools cannot exceed num_validators.")
    if num_pools <= 0:
        raise ValueError("num_pools must be >= 1.")

    total_stake = 1.0
    validators_total = total_stake * validator_frac
    delegators_total = total_stake - validators_total

    # validator self-bonds (capped)
    v_stakes = _get_shares(validators_total, num_validators, max_validator_stake, alpha=1.0)
    #v_stakes.sort(reverse=True)

    validators = []
    for i in range(num_validators):
        is_pool = (i < num_pools)  # simplest: first num_pools are pools
        commission_rate = pool_commission_rate if is_pool else 0.0
        validators.append(Validator(i, v_stakes[i], is_pool=is_pool, apr_window=apr_window, commission_rate=commission_rate))

    # delegator stakes (heavy-tailed, normalized)
    d_stakes = _lognormal_stakes(delegators_total, num_delegators, mu=delegator_mu, sigma=delegator_sigma)

    delegators = []
    for j in range(num_delegators):
        d = Delegator(j, d_stakes[j], aggressiveness=aggressiveness, loyalty=loyalty)
        delegators.append(d)

    # build world
    world = World(validators, delegators, setup, reward_per_round)

    # initial random delegation assignment
    assign_initial_delegations(world, weighted=pool_selection_weighted)

    if verbose:
        print_sanity_checks(world, max_validator_stake)

    return world

def assign_initial_delegations(world, weighted=True):
    pools = world.pools()
    if not pools:
        raise RuntimeError("No pool validators available for initial delegation.")

    weights = [v.voting_power for v in pools] if weighted else None

    for d in world.delegators:
        chosen = random.choices(pools, weights=weights, k=1)[0]
        d.bounded_validator = chosen
        chosen.add_delegator(d)

def print_sanity_checks(world, max_validator_stake):
    print("===== SANITY CHECKS =====")

    total_validator_stake = sum(v.stake for v in world.validators)
    total_delegator_stake = sum(d.stake for d in world.delegators)
    total_stake = total_validator_stake + total_delegator_stake

    print(f"Total stake in system: {total_stake:.6f}")
    print(f"  Validator self-bonded stake: {total_validator_stake:.6f}")
    print(f"  Delegator stake:             {total_delegator_stake:.6f}")

    max_v_stake = max(v.stake for v in world.validators)
    min_v_stake = max(v.stake for v in world.validators)

    print(f"Max validator self-stake:     {max_v_stake:.6f}")
    print(f"Min validator self-stake:     {min_v_stake:.6f}")
    
    print(f"Stake cap respected:          {max_v_stake <= max_validator_stake}")

    total_voting_power = sum(v.voting_power for v in world.validators)
    print(f"Total voting power (should be ~1.0): {total_voting_power:.6f}")

    pool_validators = [v for v in world.validators if v.is_pool]
    print(f"Number of pool validators:    {len(pool_validators)}")

    delegated_power = sum(
        v.voting_power - v.stake for v in pool_validators
    )
    print(f"Total delegated voting power: {delegated_power:.6f}")

    undelegated = [
        d for d in world.delegators if d.bounded_validator is None
    ]
    print(f"Delegators without validator: {len(undelegated)}")

    max_d_stake = max(v.stake for v in world.delegators)
    min_d_stake = min(v.stake for v in world.delegators)
    print(f"Max delegator stake:     {max_d_stake:.6f}")
    print(f"Min delegator stake:     {min_d_stake:.6f}")

    print("==========================")