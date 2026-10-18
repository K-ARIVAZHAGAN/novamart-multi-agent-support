# NovaMart Knowledge Base console setup

Open Amazon Bedrock → Knowledge Bases in **us-east-1**.

For each row below, create a **Self-managed** vector Knowledge Base, choose S3 as the data source, and use **Amazon Titan Embed Text v2**.

Policy document bucket: `udacity-agentcore-policy-docs-062966552587-ab401230`

Existing S3 Vectors bucket: `udacity-agentcore-vectors-062966552587-ab401230`

| Knowledge Base name | S3 data source prefix | Existing vector index |
| --- | --- | --- |
| novamart-returns-policy-kb | policies/returns/ | returns-policy-index |
| novamart-shipping-policy-kb | policies/shipping/ | shipping-policy-index |
| novamart-warranty-policy-kb | policies/warranty/ | warranty-policy-index |

Allow the console to create the Knowledge Base service role with access to the selected resources. Choose the existing vector bucket and matching index; do not choose Managed KB or create a different vector store.

After creating each KB, select its data source and **Sync**. Wait for the ingestion job to complete. Copy the **Knowledge Base ID** (not the data source ID) into the matching `RETURNS_KB_ID`, `SHIPPING_KB_ID`, or `WARRANTY_KB_ID` field in `.env`.

## Model access verification

The first Haiku 4.5 invocation returned a Marketplace access error. After waiting for activation to propagate, both required model profiles successfully responded. The course model configuration remains unchanged. See `evidence/model-and-guardrail-checks.txt` for the successful checks.
