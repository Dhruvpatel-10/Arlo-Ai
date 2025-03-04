# Arlo Voice Assistant 🎙️

A powerful voice assistant that helps you control your computer and perform various tasks hands-free. Arlo can handle everything from opening applications to web searches and system operations.

## 🌟 Features

- **Web Navigation**: Open and search across multiple platforms
  - Google Search
  - Social Media (Instagram, X.com/Twitter)
  - Custom website searches
- **System Operations**:
  - Take screenshots
  - Access webcam
  - System navigation
- **Office Integration**:
  - Microsoft Excel
  - Microsoft Word
  - Microsoft PowerPoint
- **Browser Control**: Chrome integration for web operations

## 🔧 Requirements

- Python 3.8+
- [Google Chrome](https://www.google.com/chrome/)
- Anaconda/Miniconda

### Installing Conda

If you don't have Conda installed:

1. **Download the installer**:
   - Windows: [Miniconda for Windows](https://docs.conda.io/en/latest/miniconda.html)
   - Linux: [Miniconda for Linux](https://docs.conda.io/en/latest/miniconda.html)

2. **Install Miniconda**:
   - Windows: Run the downloaded `.exe` file
   - Linux: Run in terminal:
     ```bash
     bash Miniconda3-latest-Linux-x86_64.sh
     ```

3. **Verify installation**:
   ```bash
   conda --version
   ```

## 🚀 Installation

### Set Up Conda Environment

**Virtual Environment**:
```bash
# Create and activate environment
conda env create -f env.yml
conda activate Arlo_env
```
## ⚙️ Environment Variables

This project uses a `.env` file to manage environment-specific settings like API keys and secret tokens.

### Setting Up the `.env` File

1. **Create your `.env` file**:
   ```bash
   cp .env.example .env
   ```

2. **Configure Variables**:
   - Open `.env` in your preferred text editor
   - Replace placeholder values with your actual credentials
   - Save the file

## 🎯 Running Arlo

```bash
python run.py
```

## 🔍 Troubleshooting

- If you encounter any issues after installation:
  1. Ensure Conda environment is activated
  2. Verify all environment variables are set correctly
  3. Try restarting your IDE or terminal
  3. Try restarting your IDE or terminal

## 📄 License
This project is licensed under the Apache License, Version 2.0. You may use it in compliance with the License.

You can read the full license here:
🔗 (Apache License 2.0)[https://www.apache.org/licenses/LICENSE-2.0]

Unless required by law or agreed upon in writing, this software is distributed "as is", without warranties or guarantees. See the License for more details.

## 🤝 Contributing
By contributing to this project, you agree that your contributions will be licensed under the Apache License, Version 2.0.