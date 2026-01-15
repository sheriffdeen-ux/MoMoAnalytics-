# MoMo Analytics Ghana

This is a Flask application for processing mobile money (MoMo) SMS messages from Ghanaian providers.

## Deployment with Docker

The most reliable way to run this application is with Docker. This method automatically handles all system dependencies and Python environment setup, permanently solving any issues with `mise`.

### Prerequisites

- [Docker](https://www.docker.com/get-started) installed on your system.

### Running the Application

1.  **Build the Docker image:**
    ```bash
    docker build -t momo-analytics .
    ```

2.  **Run the Docker container:**
    Replace the placeholder values with your actual secret keys.
    ```bash
    docker run -d -p 8080:8080 \
      -e TELEGRAM_BOT_TOKEN="<YOUR_TELEGRAM_BOT_TOKEN>" \
      -e TWILIO_ACCOUNT_SID="<YOUR_TWILIO_ACCOUNT_SID>" \
      -e TWILIO_AUTH_TOKEN="<YOUR_TWILIO_AUTH_TOKEN>" \
      -e TWILIO_WHATSAPP_NUMBER="<YOUR_TWILIO_WHATSAPP_NUMBER>" \
      --name momo-analytics-app \
      momo-analytics
    ```

The application will now be running and accessible at `http://localhost:8080`.
