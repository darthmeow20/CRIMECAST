# Installation Guide - CRIMECAST Sentiment Analysis

## Problem: "No module named 'textblob'"

Your sentiment analysis module needs TextBlob and NLTK libraries. Here's how to install them.

---

## ✅ Solution (Choose One)

### Option 1: Install Individual Packages (Recommended)

**From your project directory** (`C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST`):

```bash
pip install textblob nltk
```

Or if using the virtual environment:

```bash
.\.venv\Scripts\pip.exe install textblob nltk
```

### Option 2: Install from requirements.txt

We've already created a clean `requirements.txt`. Install all at once:

```bash
pip install -r requirements.txt
```

### Option 3: Install with Upgrade

If you have old versions:

```bash
pip install --upgrade textblob nltk
```

---

## 🔧 Step-by-Step Installation

### 1. Open Command Prompt/PowerShell
Navigate to your project:
```bash
cd C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST
```

### 2. Install TextBlob
```bash
pip install textblob
```

### 3. Install NLTK
```bash
pip install nltk
```

### 4. Test Installation
```bash
python -c "import textblob; print('TextBlob installed!')"
python -c "import nltk; print('NLTK installed!')"
```

### 5. Run Sentiment Analysis
```bash
python sentiment_analysis.py
```

---

## 📋 Package Details

| Package | Version | Purpose |
|---------|---------|---------|
| **textblob** | 0.17.1 | Advanced NLP sentiment analysis |
| **nltk** | 3.8.1 | Natural Language Toolkit |

---

## ✅ Verify Installation

After installing, verify everything works:

```bash
python sentiment_analysis.py
```

**Expected Output:**
```
Rows scored: 10
Sentiment output: model_outputs\sentiment_scores.csv
Label counts: {'negative': 5, 'positive': 3, 'neutral': 2}
Average polarity: -0.245
Average crime intensity: 6.50
Report generated: model_outputs\sentiment_report.txt
```

---

## 🆘 If Installation Fails

### Error: "pip command not found"
Use Python directly:
```bash
python -m pip install textblob nltk
```

### Error: Permission denied
Try with `--user` flag:
```bash
pip install --user textblob nltk
```

### Error: Network issues
Use a mirror:
```bash
pip install -i https://pypi.org/simple/ textblob nltk
```

### Using Virtual Environment (.venv)
```bash
.\.venv\Scripts\pip.exe install textblob nltk
```

---

## 🚀 After Installation

Run sentiment analysis immediately:

```bash
# Quick test with sample data
python sentiment_analysis.py

# From interactive menu
python app.py
# Choose: 4. Run sentiment scoring

# Full pipeline
python app.py --full
```

---

## 📦 All Dependencies

If you want to install ALL project dependencies:

```bash
pip install -r requirements.txt
```

This includes:
- numpy, pandas, scikit-learn (ML)
- matplotlib, seaborn (visualization)
- textblob, nltk (sentiment)
- And more...

---

## 💡 Tips

1. **Virtual Environment**: Always use `.venv\Scripts\pip.exe` if working in virtual environment
2. **Global Install**: Use `pip install` if installing globally
3. **Check Python**: Make sure you're using correct Python version:
   ```bash
   python --version
   ```
4. **Upgrade pip**: If issues persist, upgrade pip first:
   ```bash
   python -m pip install --upgrade pip
   ```

---

## ✨ Now You're Ready!

Once installed, run:
```bash
python sentiment_analysis.py
```

Your sentiment analysis will work perfectly! 🎉

---

## 📞 Quick Commands Reference

| Task | Command |
|------|---------|
| Install TextBlob & NLTK | `pip install textblob nltk` |
| Install all dependencies | `pip install -r requirements.txt` |
| Run sentiment analysis | `python sentiment_analysis.py` |
| Interactive menu | `python app.py` |
| Full pipeline | `python app.py --full` |
| Verify installation | `python -c "import textblob; print('OK')"` |

