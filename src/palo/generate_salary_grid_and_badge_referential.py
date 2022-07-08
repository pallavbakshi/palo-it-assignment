import click
import random
import pandas as pd

from typing import Dict, List, Union
from palo.main import LEVEL_NAMES

random.seed(10)

# We need to generate three tables:
# user_referential: username, hive, levelName, badgeName
# badge_referential: badgeName, badgeType, levelName, hive
# salary_grid: hive, levelName, baseSalary, rank

# badge_referential & salary_grid are like normal databases
# where we can add, delete or update rows.
# user_referential is an append only database because a
# user will keep on evolving as they progress through their
# career at Palo IT.

# NOTE: If you change any of the following parameters, you need to
# re-run the entire script.

HIVES = ["tech", "design"]
RANKS = [1, 2, 3, 4, 5]
BADGE_VALUE = {"bronze": 400, "silver": 500}

# Employees starting at Level 1 will be aiming for Level 2 badges.
# At Level 2 aiming for Level 3 badges.
# Hence, there'll be no badges for Level 1 because there is no
# Level 0.
NUMBER_BADGES_PER_RANK = {
    "2": {"bronze": 8, "silver": 9},
    "3": {"bronze": 8, "silver": 9},
    "4": {"bronze": 8, "silver": 9},
    "5": {"bronze": 8, "silver": 9},
    # Assuming you cannot have badges for Level 6
}

# You can ONLY choose the starting salary. You cannot choose
# salary for each level. This affects the data generation.
# Salary of each subsequent level follows a formula. Hence, you
# can only choose the starting point.
STARTING_BASE_SALARY = {"tech": 18000, "design": 17000}

BADGE_NAME_SEEDS = {
    "tech": [
        "Turing",
        "Stroustrup",
        "Jobs",
        "Einstein",
        "Newton",
        "Curie",
        "Lovelace",
        "Sandberg",
        "Zuckerberg",
        "Gates",
        "Brin",
        "Page",
    ],
    "design": [
        "Norman",
        "Ideo",
        "Krug",
        "Amazon",
        "Miro",
        "Notion",
        "AirBnB",
        "Spreadsheets",
        "Snapchat",
        "Instagram",
        "WhatsApp",
        "Telegram",
    ],
}

VALUEGENERAL_LIMITS = [10000, 20000]


@click.command()
@click.option(
    "--data_path",
    type=str,
    default="data",
    help="Where is the data stored? What's the path?",
)
def main(data_path):
    badge_referential = pd.DataFrame(generate_data_for_badge_referential())
    salary_grid = pd.DataFrame(generate_data_for_salary_grid())
    user_referential = pd.DataFrame(
        columns=["username", "hive", "levelName", "badgeName"]
    )
    badge_referential.to_csv(f"{data_path}/badge_referential.csv", index=False)
    salary_grid.to_csv(f"{data_path}/salary_grid.csv", index=False)
    user_referential.to_csv(f"{data_path}/user_referential.csv", index=False)


def generate_data_for_salary_grid() -> List[Dict[str, Union[str, int, float]]]:
    result = []
    for hive in HIVES:
        result.extend(create_fake_salary_grid_for_hive(hive))
    return result


def create_fake_salary_grid_for_hive(hive: str) -> List:
    result = []
    for rank, levelName in zip(RANKS, LEVEL_NAMES):
        previous_rank_salary = (
            STARTING_BASE_SALARY[hive] if not result else result[-1]["baseSalary"]
        )
        result.append(
            {
                "rank": rank,
                "levelName": levelName,
                "hive": hive,
                "baseSalary": get_salary_for_rank(rank, previous_rank_salary),
            }
        )
    return result


def get_salary_for_rank(rank: int, previous_rank_salary: float) -> float:
    # Salary for rank 1 doesn't depend upon any badge. It's the starting point.
    if rank == 1:
        return previous_rank_salary
    badge_value = get_total_badge_value(rank, "bronze") + get_total_badge_value(
        rank, "silver"
    )
    value_general = random.randrange(
        VALUEGENERAL_LIMITS[0], VALUEGENERAL_LIMITS[1], 1000
    )
    return previous_rank_salary + badge_value + value_general


def get_total_badge_value(rank: int, badge: str) -> float:
    return NUMBER_BADGES_PER_RANK[str(rank)][badge] * BADGE_VALUE[badge]


def generate_data_for_badge_referential() -> List[Dict[str, str]]:
    result = []
    for hive in HIVES:
        result.extend(create_fake_badge_referential_for_hive(hive))
    return result


def create_fake_badge_referential_for_hive(hive: str) -> List[Dict[str, str]]:
    result = []
    for rank, badges in NUMBER_BADGES_PER_RANK.items():
        for badge_type, number_badges in badges.items():
            result.extend(
                [
                    create_fake_data_for_badge(badge_type, rank, hive)
                    for _ in range(number_badges)
                ]
            )
    return result


def create_fake_data_for_badge(badge_type: str, rank: str, hive: str) -> Dict[str, str]:
    return {
        "badgeName": get_random_name(hive, badge_type, rank),
        "badgeType": badge_type,
        "levelName": LEVEL_NAMES[RANKS.index(int(rank))],
        "hive": hive,
    }


def get_random_name(hive: str, badge_type: str, rank: str) -> str:
    # name = random.sample(BADGE_NAME_SEEDS[hive], 3)
    level_name = LEVEL_NAMES[RANKS.index(int(rank))]
    rand_name = str(random.randrange(1, 10000000, 1))
    return "-".join([hive, badge_type, level_name, rand_name])


if __name__ == "__main__":
    main()
