I'm obsessive about the code I write and I know that. The kind who'll leave a PR comment asking to rename a request-body alias from "sp" to "spk", not because anyone asked, but because "spk" feels right cause I want my codebase to be PERFECT.

What I built and run at AiRA:

- the backend, from the first commit, in Python and FastAPI on MongoDB, Redis and Qdrant
- our whole Azure infrastructure on private networking, which I manage alone
- the CI/CD, where every merged PR deploys to its own slot first and is then swapped into production, so releases cause no downtime
- pipelines that sign in to Azure with OIDC, not stored secrets
- one interface over 6 LLM providers, with token and cost tracking
- an MCP server with OAuth 2.1 that lets ChatGPT and Claude work with our company's context

All of it is in private repos. Ask me about any of it.

[LinkedIn](https://www.linkedin.com/in/anandakrishnone) · [Email](mailto:anandakrishnone@gmail.com)
