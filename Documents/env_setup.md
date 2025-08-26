# Environment Variables Configuration Guide

This document outlines the required environment variables for the AI server setup. Create a `.env` file in your project root directory and configure the following variables.

## Required Environment Variables

Create a `.env` file and add the following configurations:

```env
# OpenAI API Configuration
OPENAI_KEY=your_openai_api_key_here

# AWS S3 Bucket Configuration
S3_BUCKET_PATH=your_s3_bucket_url
S3_MODEL_PATH=your_model_path_in_s3

# AWS Credentials
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key

# Stable Diffusion WebUI Instance
WEBUI_INSTANCE_IP=your_webui_instance_url
```

## Variable Descriptions

### OpenAI Configuration
- `OPENAI_KEY`: Your OpenAI API key for accessing OpenAI services

### AWS S3 Configuration
- `S3_BUCKET_PATH`: Base URL for your S3 bucket
- `S3_MODEL_PATH`: Complete URL path to your model file in S3
- `AWS_ACCESS_KEY_ID`: AWS access key for authentication
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for authentication

### Stable Diffusion WebUI
- `WEBUI_INSTANCE_IP`: URL endpoint for your Stable Diffusion WebUI API
