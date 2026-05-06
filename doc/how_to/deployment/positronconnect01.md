---
title: Deploying to Posit Connect
---

# Deploying Panel Apps on Posit Connect

This guide explains how to deploy a Panel application on Posit Connect. Posit Connect provides a managed environment for hosting Python web applications, including Panel apps, with built-in support for authentication, scaling, and dependency management.

Posit Connect now includes support for the Panel framework. Refer to the Positron documentation for the newest updates and documentaton: https://posit.co/blog/host-panel-apps-on-posit-connect Connect, you can visit our documentation on each method.

Currently, there are three ways to deploy Panel applications on Positron Connct. Please refer to the Positron doc page above for details on these methoeds.

Push Button Deployment: Deploy your application using the Posit Publisher extension
Command Line Interface: Deploy your application using your CLI with rsconnect-python
Git-Backed Deployment: Deploy your application from a Git repository

Example using the second method for illustration:

rsconnect deploy panel . \
  --entrypoint app.py
  --server SERVER_URL \
  --api-key YOUR_API_KEY \
  --title "My App" \


---

## Overview

Panel applications can be deployed to Posit Connect as Bokeh server applications. Posit Connect handles:

- Environment creation and dependency installation
- Application hosting and scaling
- Authentication and access control
- Versioning and rollback

This makes it a convenient option for deploying Panel apps in production environments without managing infrastructure manually.

---

## Prerequisites

Before deploying, ensure you have:

Support for Panel currently requires Posit Connect 2025.11.0 or newer. Refer to the Positron documentation for the latest informaton.

- Access to a Posit Connect server
- An API key for authentication
- A working Panel application
- Python installed locally

Install the Posit deployment CLI:

```bash
pip install rsconnect-python
