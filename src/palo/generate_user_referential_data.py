import csv
import click
from typing import Dict
import pandas as pd

from palo.main import LEVEL_NAMES, get_current_level, validate_username, validate_hive
from palo.data_models import User


@click.command()
@click.option(
    "--action",
    type=click.Choice(["join_user", "earn_badge", "upgrade_level"]),
    help="There are only 3 things you can do on a user.",
)
@click.option(
    "--username",
    type=str,
    help="User upon whom you're performing the action.",
    required=True,
)
@click.option(
    "--hive",
    type=click.Choice(["tech", "design"]),
    help="Which hive are you part of? Currently we support only tech and design.",
    required=True,
)
@click.option(
    "--level_name",
    type=click.Choice(LEVEL_NAMES),
    help="User upon whom you're performing the action.",
)
@click.option(
    "--badge_names",
    "-bn",
    type=str,
    multiple=True,
    help="What's the name of the badge? You can pass multiple badge names.",
)
@click.option(
    "--data_path",
    type=str,
    default="data",
    help="Where is the data stored? What's the path?",
)
def main(action, username, hive, level_name, badge_names, data_path):
    badge_referential = fetch_data(f"{data_path}/badge_referential.csv")
    user_referential = fetch_data(f"{data_path}/user_referential.csv")
    salary_grid = fetch_data(f"{data_path}/salary_grid.csv")

    # Ensure all the inputs are of correct data types
    user = User(
        username=username, hive=hive, level_name=level_name, badge_names=badge_names
    )
    # Validate hive name actually exists in our database
    validate_hive(salary_grid, user.hive)

    if action == "join_user":
        join_user(user, data_path, salary_grid, user_referential, badge_referential)
    elif action == "upgrade_level":
        upgrade_level(user, data_path, salary_grid, user_referential)
    elif action == "earn_badge":
        earn_badge(user, data_path, salary_grid, user_referential, badge_referential)
    else:
        print("Invalid input --action")


def fetch_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def join_user(
    user: User,
    path: str,
    salary_grid: pd.DataFrame,
    user_referential: pd.DataFrame,
    badge_referential: pd.DataFrame,
) -> None:
    """
    Whenever a new user joins Palo IT, we need to put them in our database.
    This function helps them put in the database correctly.
    """
    validate_new_user(user, salary_grid, user_referential, badge_referential)

    # Whenever a new user is added, they're given the badges for their starting
    # level because they've already achieved it. Now they can work for badges
    # of the next level.
    # This is the ONLY way we can differentiate new users who start at a level
    # vs old users who are the same level but don't have the badges for that
    # level.
    backfill_data_for_new_user(user, path, badge_referential)

    record = {
        "username": user.username,
        "hive": user.hive,
        "levelName": user.level_name,
    }
    # At the start, a user can receive new badges from the level above.
    for badge in user.badge_names:
        record["badgeName"] = badge
        add_record_to_database(record, path, table="user_referential")


def upgrade_level(
    user: User,
    path: str,
    salary_grid: pd.DataFrame,
    user_referential: pd.DataFrame,
) -> None:
    validate_username(user_referential, user.username)
    validate_level_name(salary_grid, user.level_name)

    # Ensure user didn't pass any badge name when upgrading
    if user.badge_names:
        raise ValueError("You can't pass badge_names when upgrading " "user level.")

    # TODO: Ensure user can be upgraded only one level at a time
    # TODO: Ensure user need to have completed tech badges of current level
    # before upgrade
    # TODO: User can't be upgraded to the same level.

    record = {
        "username": user.username,
        "hive": user.hive,
        "levelName": user.level_name,
        "badgeName": None,
    }
    add_record_to_database(record, path, table="user_referential")


def earn_badge(
    user: User,
    path: str,
    salary_grid: pd.DataFrame,
    user_referential: pd.DataFrame,
    badge_referential: pd.DataFrame,
) -> None:
    validate_username(user_referential, user.username)
    for badge in user.badge_names:
        validate_badge_name(badge_referential, badge)
    # Ensure user didn't pass any level name when earning badge. We'll get
    # levelName from the database directly.
    if user.level_name:
        raise ValueError("You can't pass level_name when earning a badge user level.")

    # TODO: Ensure same badge can't be earned twice.
    # TODO: Ensure can only be earned for current level and the next level.

    current_user_level = get_current_level(user, user_referential)

    record = {
        "username": user.username,
        "hive": user.hive,
        "levelName": current_user_level,
    }
    for badge in user.badge_names:
        record["badgeName"] = badge
        add_record_to_database(record, path, table="user_referential")


def validate_new_user(
    user: User,
    salary_grid: pd.DataFrame,
    user_referential: pd.DataFrame,
    badge_referential: pd.DataFrame,
) -> None:
    # Ensure this user doesn't exist in the database.
    if (
        user.username
        in user_referential.loc[user_referential["hive"] == user.hive]["username"]
    ):
        raise ValueError(f"This user {user.username} already exists in the {user.hive}")
    # level_name is required for each user. A new user can't be added without
    # a level_name
    assert user.level_name is not None
    validate_level_name(salary_grid, user.level_name)

    # A new user can be added without a badge. In that case, for loop will not run.
    # However, if a badge is specified, then we need to validate it.
    for badge in user.badge_names:
        validate_badge_name(badge_referential, badge)


def validate_badge_name(badge_referential: pd.DataFrame, badge_name: str) -> None:
    if badge_name not in badge_referential["badgeName"].values:
        raise Exception(
            f"badgeName {badge_name} not found in the database."
            "Either change the badge_name or add it to the database."
        )


def validate_level_name(salary_grid: pd.DataFrame, level_name: str) -> None:
    if level_name not in salary_grid["levelName"].values:
        raise Exception(
            f"levelName {level_name} not found in the database."
            "Either change the level_name or add it to the database."
        )


def backfill_data_for_new_user(
    user: User, path: str, badge_referential: pd.DataFrame
) -> None:
    badge_names_for_current_user_level = badge_referential.loc[
        (badge_referential["levelName"] == user.level_name)
        & (badge_referential["hive"] == user.hive)
    ]["badgeName"]
    record = {
        "username": user.username,
        "hive": user.hive,
        "levelName": user.level_name,
    }
    for badge in badge_names_for_current_user_level:
        record["badgeName"] = badge
        add_record_to_database(record, path, table="user_referential")


def add_record_to_database(record: Dict[str, str], path: str, table=None):
    if table is None:
        raise Exception("You forgot to pass table in the parameter.")
    file_path = f"{path}/{table}.csv"

    # Appending to the end of the csv file.
    # We want to automatically get the headers from the CSV file
    header = None
    with open(file_path, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
    # add row to CSV file
    with open(file_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writerow(record)


if __name__ == "__main__":
    main()
