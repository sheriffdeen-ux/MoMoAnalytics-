# Railway Deployment Guide

This guide provides step-by-step instructions for deploying the MoMo Analytics application on Railway.

## Prerequisites

1.  A [Railway](https://railway.app/) account.
2.  Your code pushed to a GitHub repository.

## Step 1: Create a New Project on Railway

1.  Log in to your Railway dashboard.
2.  Click the **New Project** button.
3.  Select **Deploy from GitHub repo**.
4.  Choose the repository containing your application code.

## Step 2: Configure the Service

Railway will automatically detect the `Dockerfile` in your repository and start building the application. While it's building, you need to configure the service and add your secret environment variables.

1.  In your Railway project, you will see a new service. Click on it to open its settings.
2.  Go to the **Variables** tab.

## Step 3: Add Your Secret Environment Variables

This is the most important step for ensuring your application works correctly. You will add your Telegram and Twilio credentials here. This is a secure way to provide your secrets to the application without writing them in the code.

Click the **+ New Variable** button for each of the secrets below and add the following:

| Variable Name               | Value                                       |
| --------------------------- | ------------------------------------------- |
| `TELEGRAM_BOT_TOKEN`        | `<YOUR_TELEGRAM_BOT_TOKEN>`                  |
| `TWILIO_ACCOUNT_SID`        | `<YOUR_TWILIO_ACCOUNT_SID>`                  |
| `TWILIO_AUTH_TOKEN`         | `<YOUR_TWILIO_AUTH_TOKEN>`                   |
| `TWILIO_WHATSAPP_NUMBER`    | `<YOUR_TWILIO_WHATSAPP_NUMBER>`              |

You can also add other variables from the `Config` class in `final_system.py` if you need to override their default values, for example:
- `SECRET_KEY` (recommended for production)
- `DATABASE_URL` (if you want to use a Railway-provided PostgreSQL database)

## Step 4: Set Up the Web Service

1.  Go to the **Settings** tab for your service.
2.  Under the **Networking** section, click **Generate Domain** to get a public URL for your application. Railway will automatically handle the `PORT` for you.

## Step 5: Finalize and Go Live

Once the build is complete, your application will be deployed and available at the generated domain. You can view the deployment logs in the **Deployments** tab to ensure everything started correctly.

Your MoMo Analytics application is now live on Railway!
