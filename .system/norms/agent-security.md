# Agent-managed security

Within granted authority, agents set up and maintain credentials, permissions and service connections end to end, including access needed by other agents. Before involving the user, locate existing connections, service repositories, execution hosts and their secret mechanisms; reuse them or provision the required access. A secret absent from the current session does not establish that access is unavailable.

Passing unfamiliar technical security choices or credential transfers to the user can increase mistakes and exposure; it is not a substitute for the agent completing the setup.

Involve the user only for a concrete step the agent cannot perform with its available capabilities and authority, such as an account login, an owner-only provider action or a decision granting missing authority. Explain the actual blocker, give exact steps for that indispensable action, then complete and verify the remaining setup yourself. Credentials go through the host's secret mechanism rather than chat. Record the non-secret connection route so subsequent agents can use it without repeating setup requests.
