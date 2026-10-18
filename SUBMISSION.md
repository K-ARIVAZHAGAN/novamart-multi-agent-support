# NovaMart submission notes

The unmodified course suite passed **120/120 points**. Full output is in `evidence/all-tests.txt`.

## Included implementation and evidence

- `src/agent_orchestrator.py`: worker agents, parallel RAG, orchestration, versioned guardrail, CLI runtime deployment, session-summary memory, and observability.
- `.env`: deployed resource identifiers and settings; no AWS access keys, secret keys, or session tokens.
- `evidence/live-scenarios.txt`: real local return, policy, and arithmetic conversations with X-Ray trace identifiers.
- `evidence/deployed-runtime-invoke.txt`: successful policy response from the deployed runtime.
- `evidence/service-map.json`: service graph retrieved from AWS X-Ray, including the connected orchestrator, workers, and all three Knowledge Base nodes. This supports the required Console screenshot and does not replace it.
- `evidence/model-and-guardrail-checks.txt`: both required models respond; arithmetic input and output are allowed, while negotiation, competitor-product requests, and legal threats are blocked.
- `evidence/refund-tool-checks.txt`: expired return rejection, duplicate return protection, and customer/order isolation checks using fictional seed records.

The course helpers, configuration module, and tests remain unchanged. Runtime configuration files were updated by the supplied AgentCore CLI. The additional `infrastructure/setup_knowledge_bases.py` automates the same self-managed KB settings described in the classroom; all three KBs use the foundation stack's existing S3 Vectors bucket and matching indexes, with synced data sources.

## Required screenshots included

1. `evidence/tests-120.png`: actual terminal screenshot showing `120/120 pts (100%)` after the full suite.
2. `evidence/xray-service-map.png`: actual AWS Console screenshot showing the connected orchestrator, all four workers, and all three Knowledge Base nodes.

Transaction Search can take around ten minutes to index traces after first activation. If the graph is empty, wait for indexing, run the live scenarios again, then select a time range covering that invocation. A diagram drawn from the architecture is not a substitute for the actual AWS screenshot.

Run these commands from this folder in PowerShell:

```powershell
$env:AWS_PROFILE = 'udacity'
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe tests/test_agent.py all
.\.venv\Scripts\python.exe src/agent_orchestrator.py test
```

If using the ZIP on a new machine, create a Python 3.12 virtual environment and install `requirements.txt` first. Temporary AWS credentials must be configured outside the project.

## Deployment notes

An initial Haiku invocation returned an access error; it succeeded after activation propagated, without changing the required model. Interrupted npm installs were repaired using a clean dependency installation, retaining the course's CLI version 0.30.0 and pinned CDK dependencies. One stalled S3 multipart asset upload was resumed from the exact CLI-generated package; runtime creation and updates were performed through the required CLI.

The return scenario intentionally asks for a missing customer-provided reason before initiating a return. The backend independently checks the customer/order pair, delivered status, tier window, and duplicate reference before writing the fictional order record.

Resources remain available for screenshots and review. Run the supplied cleanup only after submission and after saving all evidence. The extra KB helper creates IAM role `novamart-policy-kb-role` with inline policy `NovaMartKnowledgeBaseAccess`; remove that role after the three KBs have been deleted if the supplied cleanup does not remove it.
