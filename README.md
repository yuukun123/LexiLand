# LexiLand

**LexiLand** is an English vocabulary learning application that helps users **add, manage, and practice vocabulary** effectively. The app supports learning by **topics**, repeated practice, and prioritizes difficult words to help users **remember longer**.

---

## Key Features

### 1. Add Vocabulary
- Users can add new English words to the app.
- The app automatically **renders the Vietnamese meaning** for each word.
- Vocabulary can be **organized by topic** for easier management and practice.

### 2. Topic Management
- Each word is added under a specific topic.
- Users can create multiple topics for different groups of words (e.g., Food, Travel, Business…).
- Supports viewing, editing, and deleting words within each topic.

### 3. Vocabulary Practice
- Supports practicing **one or multiple topics**.
- Words are practiced using **repeated sessions** (spaced repetition) to improve long-term memory.
- Words that users **frequently get wrong are prioritized**, appearing more often in practice sessions.
- User-friendly and intuitive practice interface.

### 4. Progress Tracking
- Track learning progress by topic.
- Shows words that are **already remembered**, **mastered**, or **need more practice**, helping users focus on what they need to learn next.

---

## Technologies Used
- **Python 3.10
- **PyQt5**: GUI development
- **SQLite / Local Database**: Store vocabulary and learning progress
- **Werkzeug**: For hashing passwords or OTP functionality (if used)
- Internal modules: `src.utils`, `src.services` for handling app logic and data management

---

## Installation
1. Clone the repository:

```bash
git clone https://github.com/yuukun123/LexiLand.git
cd LexiLand
```

2. Write this code in terminal:
```bash
pip install -r requirements.txt
```

3. run file:
```bash
python main.py
