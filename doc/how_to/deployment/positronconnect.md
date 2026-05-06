---
title: Deploying to Posit Connect
---

# Deploying Panel Apps on Posit Connect

This guide explains how to deploy a Panel application on Posit Connect. Posit Connect provides a managed environment for hosting Python web applications, including Panel apps, with built-in support for authentication, scaling, and dependency management.

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

- Access to a Posit Connect server
- An API key for authentication
- A working Panel application
- Python installed locally

Install the Posit deployment CLI:

```bash
pip install rsconnect-python
