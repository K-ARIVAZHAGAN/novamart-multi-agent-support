"""Create and sync NovaMart KBs against the foundation's existing S3 Vectors indexes.

Uses the same settings as the classroom console workflow. Run with AWS_PROFILE set;
credentials are read by boto3 and are never written to project files.
"""
import json
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import set_key

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config


def main():
    region = config.AWS_REGION
    account = config.ACCOUNT_ID
    iam = boto3.client('iam', region_name=region)
    kb = boto3.client('bedrock-agent', region_name=region)
    role_name = 'novamart-policy-kb-role'
    trust = {'Version': '2012-10-17', 'Statement': [{
        'Effect': 'Allow', 'Principal': {'Service': 'bedrock.amazonaws.com'},
        'Action': 'sts:AssumeRole', 'Condition': {'StringEquals': {'aws:SourceAccount': account},
        'ArnLike': {'aws:SourceArn': f'arn:aws:bedrock:{region}:{account}:knowledge-base/*'}}}]}
    try:
        role = iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust))['Role']
    except iam.exceptions.EntityAlreadyExistsException:
        role = iam.get_role(RoleName=role_name)['Role']
    vector_bucket = config.VECTOR_STORE_BUCKET_ARN
    policy_bucket = config.POLICY_BUCKET
    policy = {'Version': '2012-10-17', 'Statement': [
        {'Effect': 'Allow', 'Action': ['bedrock:InvokeModel'],
         'Resource': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0'},
        {'Effect': 'Allow', 'Action': ['s3:ListBucket'], 'Resource': f'arn:aws:s3:::{policy_bucket}'},
        {'Effect': 'Allow', 'Action': ['s3:GetObject'], 'Resource': f'arn:aws:s3:::{policy_bucket}/policies/*'},
        {'Effect': 'Allow', 'Action': ['s3vectors:GetIndex', 's3vectors:PutVectors', 's3vectors:GetVectors',
                                    's3vectors:DeleteVectors', 's3vectors:QueryVectors', 's3vectors:ListVectors'],
         'Resource': f'{vector_bucket}/index/*'},
    ]}
    iam.put_role_policy(RoleName=role_name, PolicyName='NovaMartKnowledgeBaseAccess', PolicyDocument=json.dumps(policy))
    existing = {item['name']: item['knowledgeBaseId'] for page in kb.get_paginator('list_knowledge_bases').paginate()
                for item in page.get('knowledgeBaseSummaries', [])}
    jobs = []
    for domain in ('returns', 'shipping', 'warranty'):
        name = f'novamart-{domain}-policy-kb'
        kb_id = existing.get(name)
        if not kb_id:
            for attempt in range(12):
                try:
                    response = kb.create_knowledge_base(
                        name=name, roleArn=role['Arn'],
                        knowledgeBaseConfiguration={'type': 'VECTOR', 'vectorKnowledgeBaseConfiguration': {
                            'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0'}},
                        storageConfiguration={'type': 'S3_VECTORS', 's3VectorsConfiguration': {
                            'vectorBucketArn': vector_bucket, 'indexName': f'{domain}-policy-index'}})
                    kb_id = response['knowledgeBase']['knowledgeBaseId']
                    break
                except ClientError as exc:
                    if attempt == 11 or not any(word in str(exc).lower() for word in ('role', 'assume', 'permission')):
                        raise
                    time.sleep(5)
        set_key(str(ROOT / '.env'), f'{domain.upper()}_KB_ID', kb_id)
        print(f'{domain}: {kb_id}', flush=True)
        for _ in range(60):
            status = kb.get_knowledge_base(knowledgeBaseId=kb_id)['knowledgeBase']['status']
            if status == 'ACTIVE':
                break
            if status in ('FAILED', 'DELETE_UNSUCCESSFUL'):
                raise RuntimeError(f'{domain} Knowledge Base failed: {status}')
            time.sleep(5)
        else:
            raise TimeoutError(f'{domain} Knowledge Base did not become ACTIVE')
        sources = kb.list_data_sources(knowledgeBaseId=kb_id).get('dataSourceSummaries', [])
        source_id = sources[0]['dataSourceId'] if sources else kb.create_data_source(
            knowledgeBaseId=kb_id, name=f'{domain}-policy-documents',
            dataSourceConfiguration={'type': 'S3', 's3Configuration': {
                'bucketArn': f'arn:aws:s3:::{policy_bucket}', 'inclusionPrefixes': [f'policies/{domain}/']}})['dataSource']['dataSourceId']
        job = kb.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=source_id)['ingestionJob']
        jobs.append((domain, kb_id, source_id, job['ingestionJobId']))
    for domain, kb_id, source_id, job_id in jobs:
        for _ in range(120):
            job = kb.get_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=source_id, ingestionJobId=job_id)['ingestionJob']
            if job['status'] == 'COMPLETE':
                print(f'{domain}: sync COMPLETE; {job.get("statistics", {})}', flush=True)
                break
            if job['status'] in ('FAILED', 'STOPPED'):
                raise RuntimeError(f'{domain}: {job}')
            time.sleep(5)
        else:
            raise TimeoutError(f'{domain}: sync timed out')


if __name__ == '__main__':
    main()
