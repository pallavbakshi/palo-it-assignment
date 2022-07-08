import click
from typing import List, Optional
import pandas as pd

from palo.data_models import User

# Assumptions:
# You cannot have duplicate badge names
# A user can get multiple badges at the same time.

LEVEL_NAMES = ["Junior", "Mid", "Senior", "Team_Lead", "Director"]


@click.command()
@click.option(
    "--username",
    type=str,
    help="User for whom you want to calculate salary for.",
    required=True,
)
@click.option(
    "--hive",
    type=click.Choice(["tech", "design"]),
    help="Which hive are you part of? Currently we support only tech and design.",
    required=True,
)
@click.option(
    "--data_path",
    type=str,
    default="data",
    help="Where is the data stored? What's the path?",
)
def main(username, hive, data_path):
    badge_referential = fetch_data(f"{data_path}/badge_referential.csv")
    user_referential = fetch_data(f"{data_path}/user_referential.csv")
    salary_grid = fetch_data(f"{data_path}/salary_grid.csv")

    # Ensure all the inputs are of correct data types
    user = User(
        username=username, hive=hive, level_name=None, badge_names=None
    )
    # Validate hive name exists in our database
    validate_hive(salary_grid, user.hive)
    # validate username exists in our database
    validate_username(user_referential, user.username)

    salary = calculate_salary(user, salary_grid, user_referential, badge_referential)


def calculate_salary(
    user: User,
    salary_grid: pd.DataFrame,
    user_referential: pd.DataFrame,
    badge_referential: pd.DataFrame,
) -> float:
    level_name = get_current_level(user, user_referential)
    base_salary = get_base_salary(level_name, salary_grid, user)

    total_badge_value_for_current_level = get_badge_value(
        level_name, salary_grid, badge_referential, user_referential, user, total=True
    )
    badge_value_from_current_level = get_badge_value(
        level_name, salary_grid, badge_referential, user_referential, user, total=False
    )
    yet_to_complete_badge_value = (
        total_badge_value_for_current_level - badge_value_from_current_level
    )

    badge_value_from_next_level = get_badge_value_for_next_level(
        level_name, salary_grid, badge_referential, user_referential, user
    )

    salary = base_salary - yet_to_complete_badge_value + badge_value_from_next_level
    print(salary, base_salary, yet_to_complete_badge_value, badge_value_from_next_level)
    return salary


def get_current_level(user: User, user_referential: pd.DataFrame) -> str:
    current_user_level = user_referential.loc[
        (user_referential["username"] == user.username)
        & (user_referential["hive"] == user.hive)
    ]["levelName"].values[-1]
    assert current_user_level is not None
    return current_user_level


def get_base_salary(level_name: str, salary_grid: pd.DataFrame, user: User) -> float:
    base_salary = salary_grid.loc[
        (salary_grid["levelName"] == level_name) & (salary_grid["hive"] == user.hive)
    ]["baseSalary"].values[0]
    return float(base_salary)


def get_badge_value(
    level_name: str,
    salary_grid: pd.DataFrame,
    badge_referential: pd.DataFrame,
    user_referential: pd.DataFrame,
    user: User,
    total: bool = False,
) -> float:
    base_salary_current_level = get_base_salary(level_name, salary_grid, user)
    previous_level_name = LEVEL_NAMES[LEVEL_NAMES.index(level_name) - 1]
    base_salary_previous_level = get_base_salary(previous_level_name, salary_grid, user)

    salary_differential = base_salary_current_level - base_salary_previous_level
    if total:
        return 0.5 * salary_differential

    total_bronze_for_current_level = len(
        get_all_badges(level_name, user.hive, "bronze", badge_referential)
    )
    value_bronze = ((salary_differential * 0.5) / total_bronze_for_current_level) * 0.4

    total_silver_for_current_level = len(
        get_all_badges(level_name, user.hive, "silver", badge_referential)
    )
    value_silver = ((salary_differential * 0.5) / total_silver_for_current_level) * 0.6

    bronze_earned_by_user = get_badges_earned(
        level_name, user, "bronze", badge_referential, user_referential
    )
    silver_earned_by_user = get_badges_earned(
        level_name, user, "silver", badge_referential, user_referential
    )

    return (
        len(bronze_earned_by_user) * value_bronze
        + len(silver_earned_by_user) * value_silver
    )


def get_badge_value_for_next_level(
    level_name: str,
    salary_grid: pd.DataFrame,
    badge_referential: pd.DataFrame,
    user_referential: pd.DataFrame,
    user: Optional[User] = None,
) -> float:
    # Adding 1 to counter zero indexing
    rank = LEVEL_NAMES.index(level_name) + 1
    # There are no badges to receive after Level 5. A user at Level 5 cannot receive any
    # more badges from Level 6 because Level 6 doesn't exist.
    if rank < 5:
        # Removing 1 because python follows zero-indexing which we changed before
        rank = rank - 1
        # Next rank will be previous rank + 1
        next_level_name = LEVEL_NAMES[rank + 1]
        badge_value_from_next_level = get_badge_value(
            next_level_name, salary_grid, badge_referential, user_referential, user
        )
    else:
        badge_value_from_next_level = 0.0
    return badge_value_from_next_level


def get_all_badges(
    level_name: str,
    hive: str,
    badge_type: str,
    badge_referential: pd.DataFrame,
) -> List[str]:
    badges_in_level = badge_referential.loc[
        (badge_referential["hive"] == hive)
        & (badge_referential["levelName"] == level_name)
        & (badge_referential["badgeType"] == badge_type)
    ]["badgeName"].values
    return [x for x in badges_in_level]


def get_badges_earned(
    level_name: str,
    user: User,
    badge_type: str,
    badge_referential: pd.DataFrame,
    user_referential: pd.DataFrame,
) -> List[str]:
    badges_earned = user_referential.loc[
        (user_referential["username"] == user.username)
        & (user_referential["hive"] == user.hive)
    ]["badgeName"].values
    badges_in_level = get_all_badges(
        level_name, user.hive, badge_type, badge_referential
    )
    return [x for x in badges_in_level if x in badges_earned]


def fetch_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def validate_hive(salary_grid: pd.DataFrame, hive: str) -> None:
    if hive not in salary_grid["hive"].values:
        raise Exception(
            f"hive {hive} not found in the database."
            "Either change the hive argument or add it to the database."
        )


def validate_username(user_referential: pd.DataFrame, username: str) -> None:
    if username not in user_referential["username"].values:
        raise Exception(
            f"username {username} not found in the database."
            "Either change the username argument or add it to the database."
        )


if __name__ == "__main__":
    main()
