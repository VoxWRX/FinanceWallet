#!/bin/bash
source venv/bin/activate

echo "Finding customtkinter location..."
CTK_LOCATION=$(python -c "import customtkinter, os; print(os.path.dirname(customtkinter.__file__))")

echo "Building macOS application..."
pyinstaller --noconfirm --onedir --windowed --name "Finance Wallet" \
    --add-data="${CTK_LOCATION}:customtkinter/" \
    --add-data="themes:themes/" \
    app.py

echo "Build complete! Check the 'dist' folder."
