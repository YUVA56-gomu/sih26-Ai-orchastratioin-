from dotenv import load_dotenv

load_dotenv()

from app.workflows.orca_workflow import orca_workflow


# ADK Web loads this variable.
root_agent = orca_workflow
