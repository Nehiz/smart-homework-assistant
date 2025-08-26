
# 📖 Smart Homework Assistant – Technical Documentation

## 1. Overview

The **Smart Homework Assistant** is an AI-powered educational tool designed to help kids practice mathematics (e.g., abacus, mental math, and arithmetic) in a supportive way.  

It provides:

- A **frontend interface** (Netlify-hosted) where students type their homework questions.  
- A **backend API** powered by **AWS Lambda + API Gateway**.  
- An **AI engine** (OpenAI GPT) that analyzes the question and returns **guidance** instead of just the final answer.  

---

## 2. Project Architecture

```mermaid
flowchart LR
    A[Frontend - Netlify] --> B[API Gateway]
    B --> C[AWS Lambda - Python]
    C --> D[OpenAI API - AI Processing]
    D --> A

Flow:

    1. Student submits a math problem via the frontend.

    2. API Gateway routes the request to AWS Lambda.

    3. Lambda processes the question and calls OpenAI API.

    4. AI generates a structured explanation and response.

    5. The result is sent back to the frontend for display.

----

## 3. AWS Lambda Code (File: lambda_function.py)

```python

import json
import openai

def lambda_handler(event, context):
    body = json.loads(event["body"])
    question = body.get("question", "")

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a kind math tutor. Guide kids to solve math step-by-step without just giving answers."},
            {"role": "user", "content": question}
        ]
    )

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "answer": response["choices"][0]["message"]["content"]
        })
    }


---
## 4a. API Gateway Configuration

---

Endpoint (example):
https://xxxx.execute-api.us-east-1.amazonaws.com/dev/process-homework

Method:
POST

Headers:

```json

{
  "Content-Type": "application/json",
  "x-api-key": "your-demo-api-key"
}


Sample Request:

{ "question": "What is 25 + 17?" }


Sample Response:

{ "answer": "Think of 25 as 20 + 5. Then add 17 (10 + 7). First 20 + 10 = 30, then 5 + 7 = 12. Finally, 30 + 12 = 42." }

## 4b. CORS Configuration
To enable CORS in API Gateway, the following configurations are applied:
- **Integration Response Parameters** (File: integration-response-params.json):

{
    "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods": "'GET,POST,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin": "'*'"
}

- **Method Response Parameters** (File: method-response-params.json):

{
    "method.response.header.Access-Control-Allow-Headers": true,
    "method.response.header.Access-Control-Allow-Methods": true,
    "method.response.header.Access-Control-Allow-Origin": true
}

----
## 5. Frontend Code (File: index.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Smart Homework Assistant</title>
</head>
<body>
  <h1>Smart Homework Assistant</h1>
  <input type="text" id="question" placeholder="Type your homework question...">
  <button onclick="sendQuestion()">Ask</button>
  <p id="result"></p>

  <script>
    async function sendQuestion() {
      const question = document.getElementById("question").value;

      const response = await fetch("https://xxxx.execute-api.us-east-1.amazonaws.com/dev/process-homework", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": "your-api-key"
        },
        body: JSON.stringify({ question })
      });

      const data = await response.json();
      document.getElementById("result").innerText = data.answer;
    }
  </script>
</body>
</html>

---
## 6. Deployment Guide

Backend (AWS)

    1. Create a Lambda function in AWS → upload lambda_function.py.

    2. Add your OpenAI API key as an environment variable.

    3. Connect Lambda to API Gateway → create a POST method /process-homework.

    4. Enable CORS and add an API key.

Frontend (Netlify)

    1. Push your frontend code to GitHub.

    2. Connect repo to Netlify → auto-deploy.

    3. Update fetch() in index.html with your API Gateway URL.

#7. Troubleshooting & Tips

    CORS errors: Ensure Access-Control-Allow-Origin: "*" is in your Lambda response headers.

    500 errors: Check if your Lambda has the correct environment variables.

    Slow responses: Use GPT-3.5 for faster, cheaper responses.

    Security: Rotate API keys regularly and avoid exposing real OpenAI key to frontend.

#8. Future Improvements

    User authentication ( parents and student accounts).

    Progress tracking and analytics.

    Gamification (badges, points, leaderboards).

    Expanded Support for subjects beyond math.

    Multilingual support for global reach

👨‍💻 Author: Nehis - Pioneer AI Academy Intern (nehikhareefehi@gmail.com)
📅 Last Updated: August 2025
🔗 Linked Repo: https://github.com/Nehiz/smart-homework-assistant
