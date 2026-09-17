# Personal Finance Wallet (PPBT)

A lightweight, local, multi-user desktop application for managing your personal finances. Built with Python, CustomTkinter, and SQLite.

## Features
- **Multi-User Profiles**: Secure login and distinct databases (`wallet_{username}.db`) for every user.
- **Interactive Calendar Home**: Add transactions on any date directly from the calendar UI.
- **Budget Alerts**: Set budget limits on categories and get warned if you overspend.
- **Tagging**: Categorize your expenses with flexible tags.
- **Data Export**: Export your transactions and reports cleanly to Excel files in the `exports/` folder.
- **Dynamic Reports**: Interactive matplotlib charts for monthly and annual income vs. expenses.

## Running Locally

1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python3 app.py
   ```

## Running with Docker (macOS)

Since this is a desktop GUI application, running it inside Docker requires X11 forwarding. On macOS, this means you need XQuartz.

1. **Install XQuartz** (if you don't have it):
   ```bash
   brew install --cask xquartz
   ```
2. **Configure XQuartz**:
   - Open XQuartz.
   - Go to Settings -> Security -> Check "Allow connections from network clients".
   - Restart your Mac (or log out and log back in).

3. **Build the Docker Image**:
   ```bash
   docker build -t finance-wallet .
   ```

4. **Run the Container**:
   Ensure XQuartz is running. Open a terminal and allow local connections:
   ```bash
   xhost + 127.0.0.1
   ```
   Then run the container:
   ```bash
   docker run -it --rm \
       -e DISPLAY=host.docker.internal:0 \
       -v /tmp/.X11-unix:/tmp/.X11-unix \
       -v $(pwd)/exports:/app/exports \
       finance-wallet
   ```
   *(Note: Databases will be created inside the container unless you also mount a volume for them).*
