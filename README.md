# Nalanda Central Library Catalog & Circulation Management System

A modern, full-featured web application built with **Flask** and **SQLite3** implementing the complete relational library schema with Indian literature, Indian patron records, and Indian Rupee (₹ INR) currency.

---

## 🏛️ Implemented Database Schema (11 Tables)

The application strictly implements all 11 requested relations with foreign key constraints, cascade triggers, and composite keys:

1. **`member`** (`member_id`, `name`, `address`, `phone`, `email`, `membership_date`)
2. **`librarian`** (`librarian_id`, `name`, `phone`, `email`)
3. **`publisher`** (`publisher_id`, `publisher_name`, `address`, `phone`)
4. **`category`** (`category_id`, `category_name`)
5. **`book`** (`book_id`, `title`, `ISBN`, `edition`, `year_`, `publisher_id`, `category_id`)
   - `FOREIGN KEY (publisher_id) REFERENCES publisher(publisher_id)`
   - `FOREIGN KEY (category_id) REFERENCES category(category_id)`
6. **`author`** (`author_id`, `author_name`, `nationality`)
7. **`book_author`** (`book_id`, `author_id`)
   - Composite Primary Key: `(book_id, author_id)`
   - Many-to-many relationship supporting multi-author books
8. **`shelf`** (`shelf_id`, `floor`, `section`)
9. **`book_copy`** (`copy_id`, `book_id`, `shelf_id`, `status`)
   - Tracks physical copies of books with status (`Available`, `Borrowed`, `Maintenance`, `Lost`)
   - `FOREIGN KEY (shelf_id) REFERENCES shelf(shelf_id)`
10. **`borrow`** (`borrow_id`, `member_id`, `copy_id`, `issue_date`, `due_date`, `return_date`, `fine_amount`)
    - Tracks loans, due dates, returns, and overdue fine calculation (₹5.00/day late in INR)
11. **`manages`** (`librarian_id`, `copy_id`)
    - Composite Primary Key: `(librarian_id, copy_id)`
    - Tracks staff responsibilities over individual book copies

---

## ✨ Features & User Experience

- **Executive Dashboard**:
  - Live metric KPI cards: Total Titles, Physical Copies in Stock vs. Borrowed, Active vs. Overdue Loans, and Registered Members.
  - Recent circulation feed with one-click return processing.
  - Real-time category distribution meters.

- **Book Catalog**:
  - Grid view with modern glass cards and dynamic availability indicators.
  - Multi-parameter live search (title, author, ISBN) and category filtering.
  - Comprehensive "Add Book" modal supporting multi-author selection, initial copy stock generation, and librarian assignment.

- **Deep Book Details**:
  - Complete bibliographic overview, author nationalities, publisher contact, and edition info.
  - Granular physical copies breakdown with shelf locations (Floor & Section) and assigned managing librarians (`manages`).
  - Direct "Issue Copy" button for available copies.
  - Complete historical borrow timeline per title.

- **Circulation Desk**:
  - Issue new copies to members with automatic due date computation (+14 days default).
  - Return workflow with automatic overdue detection and dynamic fine assessment.
  - Filter tabs: All Borrows, Active Loans, Overdue Loans, and Returned History.

- **Member & Staff Management**:
  - Complete Member profiles with contact information and individual borrow history.
  - Librarian profiles with copy management assignments via the `manages` relation.

- **Inventory & Shelving**:
  - Shelf directory organized by Floor and Section with real-time copy occupancy tracking.
  - Direct physical copy condition editor.

- **Schema & SQL Console**:
  - Interactive Entity Relationship (ER) cards for all 11 tables displaying column types, `[PK]` Primary Keys, and `[FK]` Foreign Keys.
  - Built-in SQL Query Runner with sample pre-set analytical queries.
  - One-click "Reset & Re-seed Clean Demo Data" button.

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.10+
- Flask (`pip install flask`)

### 2. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
**`http://127.0.0.1:5555`**

### 3. Run Automated Tests
```bash
python test_app.py
```
