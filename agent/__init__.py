"""Agent package.

`root_agent` (the Google ADK agent) is imported lazily so that the Genesis lane
(genesis_client / genesis_agent) and the offline demos can be used WITHOUT installing
google-adk. ADK tooling (`adk web`, agent/serve.py) still finds `agent.root_agent`.
"""


def __getattr__(name):
    if name == "root_agent":
        from .agent import root_agent

        return root_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
