from pathlib import Path

import dotenv


def load_dotfile(env_dir: Path, dotfile_name: str = ".env"):
    assert dotenv.load_dotenv(env_dir / dotfile_name)

def update_dotenv_variable(env_dir: Path, variable_name: str, value: str, dotfile_name: str = ".env"):
    """
    Update or add a variable in the .env file.
    :param env_dir: The directory where the .env file is located.
    :param variable_name: The name of the environment variable to update or add.
    :param value: The new value for the environment variable.
    :param dotfile_name: The name of the .env file (default is '.env').
    """
    dotenv_file = env_dir / dotfile_name

    # Read existing variables
    dotenv_vars = dotenv.dotenv_values(dotenv_file)
    dotenv_vars[variable_name] = value  # Update or add the variable

    # Write updated variables back to the .env file
    with open(dotenv_file, "w") as f:
        for key, val in dotenv_vars.items():
            f.write(f"{key}={val}\n")
    print(f"Updated {variable_name} in {dotfile_name}.")

def delete_dotenv_variable(env_dir: Path, variable_name: str, dotfile_name: str = ".env"):
    """
    Delete a variable from the .env file.
    :param env_dir: The directory where the .env file is located.
    :param variable_name: The name of the environment variable to delete.
    :param dotfile_name: The name of the .env file (default is '.env').
    """
    dotenv_file = env_dir / dotfile_name

    # Read existing variables
    dotenv_vars = dotenv.dotenv_values(dotenv_file)
    if variable_name in dotenv_vars:
        del dotenv_vars[variable_name]  # Remove the variable

        # Write updated variables back to the .env file
        with open(dotenv_file, "w") as f:
            for key, val in dotenv_vars.items():
                f.write(f"{key}={val}\n")
        print(f"Deleted {variable_name} from {dotfile_name}.")
    else:
        print(f"Variable {variable_name} not found in {dotfile_name}.")

# Example usage
env_directory = Path("../")
load_dotfile(env_directory)

update_dotenv_variable(env_directory, "NEW_VAR", "new_value")
delete_dotenv_variable(env_directory, "OLD_VAR")
