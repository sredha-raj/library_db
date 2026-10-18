import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'library_db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(reset=False):
    conn = get_db()
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = OFF;")

    if reset:
        tables = [
            'manages', 'borrow', 'book_copy', 'shelf', 'book_author',
            'author', 'book', 'category', 'publisher', 'librarian', 'member', 'member_'
        ]
        for tbl in tables:
            c.execute(f"DROP TABLE IF EXISTS {tbl};")

    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if 'member_' in tables:
        c.execute("DROP TABLE IF EXISTS member_;")

    # 1. member
    c.execute('''
    CREATE TABLE IF NOT EXISTS member (
        member_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        address VARCHAR(255),
        phone VARCHAR(25),
        email VARCHAR(100),
        membership_date DATE DEFAULT (DATE('now'))
    );
    ''')

    # 2. librarian
    c.execute('''
    CREATE TABLE IF NOT EXISTS librarian (
        librarian_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(25),
        email VARCHAR(100)
    );
    ''')

    # 3. publisher
    c.execute('''
    CREATE TABLE IF NOT EXISTS publisher (
        publisher_id INTEGER PRIMARY KEY AUTOINCREMENT,
        publisher_name VARCHAR(100) NOT NULL,
        address VARCHAR(255),
        phone VARCHAR(25)
    );
    ''')

    # 4. category
    c.execute('''
    CREATE TABLE IF NOT EXISTS category (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name VARCHAR(100) NOT NULL UNIQUE
    );
    ''')

    # 5. book
    c.execute('''
    CREATE TABLE IF NOT EXISTS book (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(150) NOT NULL,
        ISBN VARCHAR(50) UNIQUE,
        edition VARCHAR(50),
        year_ INTEGER,
        publisher_id INTEGER,
        category_id INTEGER,
        FOREIGN KEY(publisher_id) REFERENCES publisher(publisher_id) ON DELETE SET NULL,
        FOREIGN KEY(category_id) REFERENCES category(category_id) ON DELETE SET NULL
    );
    ''')

    # 6. author
    c.execute('''
    CREATE TABLE IF NOT EXISTS author (
        author_id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_name VARCHAR(100) NOT NULL,
        nationality VARCHAR(50)
    );
    ''')

    # 7. book_author
    c.execute('''
    CREATE TABLE IF NOT EXISTS book_author (
        book_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        PRIMARY KEY(book_id, author_id),
        FOREIGN KEY(book_id) REFERENCES book(book_id) ON DELETE CASCADE,
        FOREIGN KEY(author_id) REFERENCES author(author_id) ON DELETE CASCADE
    );
    ''')

    # 8. shelf
    c.execute('''
    CREATE TABLE IF NOT EXISTS shelf (
        shelf_id INTEGER PRIMARY KEY AUTOINCREMENT,
        floor VARCHAR(50) NOT NULL,
        section VARCHAR(50) NOT NULL
    );
    ''')

    # 9. book_copy
    c.execute('''
    CREATE TABLE IF NOT EXISTS book_copy (
        copy_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        shelf_id INTEGER,
        status VARCHAR(50) DEFAULT 'Available',
        FOREIGN KEY(book_id) REFERENCES book(book_id) ON DELETE CASCADE,
        FOREIGN KEY(shelf_id) REFERENCES shelf(shelf_id) ON DELETE SET NULL
    );
    ''')

    # 10. borrow
    c.execute('''
    CREATE TABLE IF NOT EXISTS borrow (
        borrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER NOT NULL,
        copy_id INTEGER NOT NULL,
        issue_date DATE NOT NULL DEFAULT (DATE('now')),
        due_date DATE NOT NULL,
        return_date DATE,
        fine_amount DECIMAL(10, 2) DEFAULT 0.00,
        FOREIGN KEY(member_id) REFERENCES member(member_id) ON DELETE CASCADE,
        FOREIGN KEY(copy_id) REFERENCES book_copy(copy_id) ON DELETE CASCADE
    );
    ''')

    # 11. manages
    c.execute('''
    CREATE TABLE IF NOT EXISTS manages (
        librarian_id INTEGER NOT NULL,
        copy_id INTEGER NOT NULL,
        PRIMARY KEY(librarian_id, copy_id),
        FOREIGN KEY(librarian_id) REFERENCES librarian(librarian_id) ON DELETE CASCADE,
        FOREIGN KEY(copy_id) REFERENCES book_copy(copy_id) ON DELETE CASCADE
    );
    ''')

    c.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
    conn.close()

def seed_sample_data(force=False):
    conn = get_db()
    c = conn.cursor()

    count_books = c.execute("SELECT COUNT(*) FROM book").fetchone()[0]
    if count_books >= 10 and not force:
        conn.close()
        return

    # Indian Categories
    categories = [
        "Indian Literature & Classics",
        "Science, Technology & Engineering",
        "History, Heritage & Civilization",
        "Philosophy & Spirituality",
        "Biographies & Autobiographies",
        "Contemporary Fiction & Novels",
        "General Science & Nature"
    ]
    for cat in categories:
        c.execute("INSERT OR IGNORE INTO category (category_name) VALUES (?)", (cat,))

    # Indian Publishing Houses
    publishers = [
        ("Penguin Random House India", "7th Floor, Infinity Tower C, DLF Cyber City, Gurugram, Haryana 122002", "+91-124-478-5600"),
        ("Rupa Publications", "7/16 Ansari Road, Daryaganj, New Delhi 110002", "+91-11-2327-8586"),
        ("HarperCollins Publishers India", "Building No. 10, Tower A, DLF Cyber City, Gurugram, Haryana 122002", "+91-124-404-4888"),
        ("Jaico Publishing House", "127 MG Road, Fort, Mumbai, Maharashtra 400001", "+91-22-6634-8211"),
        ("Oxford University Press India", "22 Institutional Area, Sector 62, Noida, Uttar Pradesh 201309", "+91-120-434-8000"),
        ("Tata McGraw-Hill Education", "B-4 Sector 63, Noida, Uttar Pradesh 201301", "+91-120-438-3400")
    ]
    for p in publishers:
        c.execute("""
            INSERT OR IGNORE INTO publisher (publisher_name, address, phone)
            VALUES (?, ?, ?)
        """, p)

    # Indian and World Authors
    authors = [
        ("Dr. A. P. J. Abdul Kalam", "Indian"),
        ("R. K. Narayan", "Indian"),
        ("Rabindranath Tagore", "Indian"),
        ("Sudha Murty", "Indian"),
        ("Munshi Premchand", "Indian"),
        ("Arundhati Roy", "Indian"),
        ("Ruskin Bond", "Indian"),
        ("Amitav Ghosh", "Indian"),
        ("Vikram Seth", "Indian"),
        ("Jawaharlal Nehru", "Indian"),
        ("Swami Vivekananda", "Indian"),
        ("Robert C. Martin", "American"),
        ("George Orwell", "British")
    ]
    for a in authors:
        c.execute("INSERT OR IGNORE INTO author (author_name, nationality) VALUES (?, ?)", a)

    # Library Shelves in Indian Central Library
    shelves = [
        ("Ground Floor", "Section A - Indian Literature & Classics"),
        ("Ground Floor", "Section B - Contemporary Fiction & Novels"),
        ("1st Floor", "Section C - Computer Science, IT & STEM"),
        ("1st Floor", "Section D - General Science & Engineering"),
        ("2nd Floor", "Section E - Indian History, Heritage & Archives"),
        ("2nd Floor", "Section F - Philosophy, Vedic Studies & Spirituality")
    ]
    for s in shelves:
        c.execute("INSERT OR IGNORE INTO shelf (floor, section) VALUES (?, ?)", s)

    # Indian Librarians
    librarians = [
        ("Dr. Rameshwar Shastri", "+91-98112-40192", "r.shastri@nalanda.library.in"),
        ("Sunita Deshmukh", "+91-98201-55821", "sunita.deshmukh@nalanda.library.in"),
        ("K. V. Swaminathan", "+91-94440-89102", "kv.swaminathan@nalanda.library.in"),
        ("Pooja Sengupta", "+91-98300-47120", "pooja.sengupta@nalanda.library.in")
    ]
    for l in librarians:
        c.execute("INSERT OR IGNORE INTO librarian (name, phone, email) VALUES (?, ?, ?)", l)

    # Indian Members / Patrons
    members = [
        ("Aarav Sharma", "Flat 402, Shanti Niketan, Indiranagar, Bengaluru, Karnataka 560038", "+91-98450-23401", "aarav.sharma@gmail.com", "2024-01-15"),
        ("Ananya Iyer", "12/A, Dr. Radhakrishnan Salai, Mylapore, Chennai, Tamil Nadu 600004", "+91-98401-87234", "ananya.iyer@outlook.com", "2024-02-10"),
        ("Rohan Verma", "B-14, Green Park Extension, New Delhi 110016", "+91-98102-39812", "rohan.verma@yahoo.co.in", "2024-03-01"),
        ("Sneha Reddy", "Plot 88, Jubilee Hills Road No. 36, Hyderabad, Telangana 500033", "+91-99890-54120", "sneha.reddy@gmail.com", "2024-04-12"),
        ("Vikramaditya Singh", "7 Marine Drive, Churchgate, Mumbai, Maharashtra 400020", "+91-98200-78190", "vikram.singh@gmail.com", "2024-05-20"),
        ("Meera Mukherjee", "45 Southern Avenue, Lake Market, Kolkata, West Bengal 700029", "+91-98310-90812", "meera.mukherjee@gmail.com", "2024-06-18")
    ]
    for m in members:
        c.execute("""
            INSERT OR IGNORE INTO member (name, address, phone, email, membership_date)
            VALUES (?, ?, ?, ?, ?)
        """, m)

    # Dict lookups
    cats = {row['category_name']: row['category_id'] for row in c.execute("SELECT category_name, category_id FROM category").fetchall()}
    pubs = {row['publisher_name']: row['publisher_id'] for row in c.execute("SELECT publisher_name, publisher_id FROM publisher").fetchall()}
    auths = {row['author_name']: row['author_id'] for row in c.execute("SELECT author_name, author_id FROM author").fetchall()}
    shlfs = [row['shelf_id'] for row in c.execute("SELECT shelf_id FROM shelf").fetchall()]
    libs = [row['librarian_id'] for row in c.execute("SELECT librarian_id FROM librarian").fetchall()]

    # Indian & Global Classics Books
    books_data = [
        ("Wings of Fire: An Autobiography", "978-8173711466", "Universities Press 1st Edition", 1999, "Jaico Publishing House", "Biographies & Autobiographies", ["Dr. A. P. J. Abdul Kalam"]),
        ("Ignited Minds: Unleashing the Power", "978-0143029823", "Penguin India PB", 2002, "Penguin Random House India", "Indian Literature & Classics", ["Dr. A. P. J. Abdul Kalam"]),
        ("Malgudi Days", "978-0143039655", "Classic Illustrated Edition", 1943, "Penguin Random House India", "Indian Literature & Classics", ["R. K. Narayan"]),
        ("The Guide", "978-8185986005", "Sahitya Akademi Award Edition", 1958, "Penguin Random House India", "Indian Literature & Classics", ["R. K. Narayan"]),
        ("Gitanjali (Song Offerings)", "978-8129117625", "Centenary Edition", 1912, "Rupa Publications", "Philosophy & Spirituality", ["Rabindranath Tagore"]),
        ("The Discovery of India", "978-0670058013", "Centennial Hardcover", 1946, "Oxford University Press India", "History, Heritage & Civilization", ["Jawaharlal Nehru"]),
        ("Godaan (The Gift of a Cow)", "978-8128801524", "National Classic Edition", 1936, "Rupa Publications", "Indian Literature & Classics", ["Munshi Premchand"]),
        ("The God of Small Things", "978-0143030966", "Booker Prize Edition", 1997, "Penguin Random House India", "Contemporary Fiction & Novels", ["Arundhati Roy"]),
        ("Wise and Otherwise: A Salute to Life", "978-0143062226", "Special Illustrated Edition", 2002, "Penguin Random House India", "Indian Literature & Classics", ["Sudha Murty"]),
        ("The Room on the Roof", "978-0143333333", "John Llewellyn Rhys Prize Edition", 1956, "Penguin Random House India", "Contemporary Fiction & Novels", ["Ruskin Bond"]),
        ("The Shadow Lines", "978-0195677058", "Oxford World's Classics", 1988, "Oxford University Press India", "Contemporary Fiction & Novels", ["Amitav Ghosh"]),
        ("A Suitable Boy", "978-0143422051", "30th Anniversary Deluxe", 1993, "Penguin Random House India", "Contemporary Fiction & Novels", ["Vikram Seth"]),
        ("Clean Code: Agile Software Craftsmanship", "978-9332548220", "Indian Subcontinent Edition", 2008, "Tata McGraw-Hill Education", "Science, Technology & Engineering", ["Robert C. Martin"]),
        ("1984", "978-0451524935", "Centennial Deluxe", 1949, "HarperCollins Publishers India", "Contemporary Fiction & Novels", ["George Orwell"])
    ]

    for b in books_data:
        title, isbn, edition, year, pub_name, cat_name, author_list = b
        pub_id = pubs.get(pub_name)
        cat_id = cats.get(cat_name)

        existing = c.execute("SELECT book_id FROM book WHERE ISBN = ?", (isbn,)).fetchone()
        if existing:
            book_id = existing[0]
            c.execute("""
                UPDATE book
                SET title = ?, edition = ?, year_ = ?, publisher_id = ?, category_id = ?
                WHERE book_id = ?
            """, (title, edition, year, pub_id, cat_id, book_id))
        else:
            c.execute("""
                INSERT INTO book (title, ISBN, edition, year_, publisher_id, category_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, isbn, edition, year, pub_id, cat_id))
            book_id = c.lastrowid

        for aname in author_list:
            aid = auths.get(aname)
            if aid:
                c.execute("INSERT OR IGNORE INTO book_author (book_id, author_id) VALUES (?, ?)", (book_id, aid))

        # Ensure at least 2 copies per book
        existing_copies = c.execute("SELECT COUNT(*) FROM book_copy WHERE book_id = ?", (book_id,)).fetchone()[0]
        if existing_copies == 0:
            for i in range(2):
                shelf_id = shlfs[(book_id + i) % len(shlfs)]
                c.execute("INSERT INTO book_copy (book_id, shelf_id, status) VALUES (?, ?, 'Available')", (book_id, shelf_id))
                cid = c.lastrowid
                if libs:
                    lid = libs[cid % len(libs)]
                    c.execute("INSERT OR IGNORE INTO manages (librarian_id, copy_id) VALUES (?, ?)", (lid, cid))

    # Borrows with Indian Rupee (INR) fine calculations
    all_copies = [r[0] for r in c.execute("SELECT copy_id FROM book_copy ORDER BY copy_id").fetchall()]
    all_members = [r[0] for r in c.execute("SELECT member_id FROM member ORDER BY member_id").fetchall()]

    borrows_count = c.execute("SELECT COUNT(*) FROM borrow").fetchone()[0]
    if borrows_count == 0 and len(all_copies) >= 4 and len(all_members) >= 4:
        today = datetime.now().date()
        # Borrow 1: returned on time (₹0.00 fine)
        c.execute("""
            INSERT INTO borrow (member_id, copy_id, issue_date, due_date, return_date, fine_amount)
            VALUES (?, ?, ?, ?, ?, 0.00)
        """, (all_members[0], all_copies[0], str(today - timedelta(days=28)), str(today - timedelta(days=14)), str(today - timedelta(days=15))))

        # Borrow 2: returned late (7 days late @ ₹5/day = ₹35.00 fine)
        c.execute("""
            INSERT INTO borrow (member_id, copy_id, issue_date, due_date, return_date, fine_amount)
            VALUES (?, ?, ?, ?, ?, 35.00)
        """, (all_members[1], all_copies[1], str(today - timedelta(days=30)), str(today - timedelta(days=16)), str(today - timedelta(days=9))))

        # Borrow 3: currently active (on time, due in 10 days)
        c.execute("""
            INSERT INTO borrow (member_id, copy_id, issue_date, due_date, return_date, fine_amount)
            VALUES (?, ?, ?, ?, NULL, 0.00)
        """, (all_members[2], all_copies[2], str(today - timedelta(days=4)), str(today + timedelta(days=10))))
        c.execute("UPDATE book_copy SET status = 'Borrowed' WHERE copy_id = ?", (all_copies[2],))

        # Borrow 4: currently active (overdue by 6 days @ ₹5/day = ₹30.00 fine)
        c.execute("""
            INSERT INTO borrow (member_id, copy_id, issue_date, due_date, return_date, fine_amount)
            VALUES (?, ?, ?, ?, NULL, 30.00)
        """, (all_members[3], all_copies[3], str(today - timedelta(days=20)), str(today - timedelta(days=6))))
        c.execute("UPDATE book_copy SET status = 'Borrowed' WHERE copy_id = ?", (all_copies[3],))

    conn.commit()
    conn.close()

# ----------------- REPOSITORY QUERIES -----------------

def get_dashboard_stats():
    conn = get_db()
    c = conn.cursor()
    today_str = datetime.now().date().isoformat()

    total_titles = c.execute("SELECT COUNT(*) FROM book").fetchone()[0]
    total_copies = c.execute("SELECT COUNT(*) FROM book_copy").fetchone()[0]
    available_copies = c.execute("SELECT COUNT(*) FROM book_copy WHERE status = 'Available'").fetchone()[0]
    borrowed_copies = c.execute("SELECT COUNT(*) FROM book_copy WHERE status = 'Borrowed'").fetchone()[0]
    
    active_borrows = c.execute("SELECT COUNT(*) FROM borrow WHERE return_date IS NULL").fetchone()[0]
    overdue_borrows = c.execute("SELECT COUNT(*) FROM borrow WHERE return_date IS NULL AND due_date < ?", (today_str,)).fetchone()[0]
    total_fines = c.execute("SELECT COALESCE(SUM(fine_amount), 0.0) FROM borrow").fetchone()[0]

    total_members = c.execute("SELECT COUNT(*) FROM member").fetchone()[0]
    total_librarians = c.execute("SELECT COUNT(*) FROM librarian").fetchone()[0]
    total_shelves = c.execute("SELECT COUNT(*) FROM shelf").fetchone()[0]
    total_categories = c.execute("SELECT COUNT(*) FROM category").fetchone()[0]

    # Category counts
    cat_distribution = [
        dict(row) for row in c.execute('''
            SELECT c.category_name, COUNT(b.book_id) as book_count
            FROM category c
            LEFT JOIN book b ON c.category_id = b.category_id
            GROUP BY c.category_id
            ORDER BY book_count DESC
            LIMIT 5
        ''').fetchall()
    ]

    # Recent activity
    recent_borrows = [
        dict(row) for row in c.execute('''
            SELECT b.borrow_id, b.issue_date, b.due_date, b.return_date, b.fine_amount,
                   m.name as member_name, bk.title as book_title, bc.copy_id
            FROM borrow b
            JOIN member m ON b.member_id = m.member_id
            JOIN book_copy bc ON b.copy_id = bc.copy_id
            JOIN book bk ON bc.book_id = bk.book_id
            ORDER BY b.borrow_id DESC
            LIMIT 6
        ''').fetchall()
    ]

    conn.close()
    return {
        "total_titles": total_titles,
        "total_copies": total_copies,
        "available_copies": available_copies,
        "borrowed_copies": borrowed_copies,
        "active_borrows": active_borrows,
        "overdue_borrows": overdue_borrows,
        "total_fines": float(total_fines),
        "total_members": total_members,
        "total_librarians": total_librarians,
        "total_shelves": total_shelves,
        "total_categories": total_categories,
        "cat_distribution": cat_distribution,
        "recent_borrows": recent_borrows
    }

def get_books(search=None, category_id=None, availability=None, sort_by='title_asc'):
    conn = get_db()
    c = conn.cursor()

    query = '''
        SELECT 
            b.book_id, b.title, b.ISBN, b.edition, b.year_,
            p.publisher_id, p.publisher_name,
            c.category_id, c.category_name,
            GROUP_CONCAT(DISTINCT a.author_name) AS authors,
            COUNT(DISTINCT bc.copy_id) AS total_copies,
            COUNT(DISTINCT CASE WHEN bc.status = 'Available' THEN bc.copy_id END) AS available_copies
        FROM book b
        LEFT JOIN publisher p ON b.publisher_id = p.publisher_id
        LEFT JOIN category c ON b.category_id = c.category_id
        LEFT JOIN book_author ba ON b.book_id = ba.book_id
        LEFT JOIN author a ON ba.author_id = a.author_id
        LEFT JOIN book_copy bc ON b.book_id = bc.book_id
        WHERE 1=1
    '''
    params = []

    if search:
        search_param = f"%{search.strip()}%"
        query += ''' AND (
            b.title LIKE ? OR
            b.ISBN LIKE ? OR
            a.author_name LIKE ? OR
            p.publisher_name LIKE ? OR
            c.category_name LIKE ?
        )'''
        params.extend([search_param, search_param, search_param, search_param, search_param])

    if category_id:
        query += " AND b.category_id = ?"
        params.append(category_id)

    query += " GROUP BY b.book_id"

    if availability == 'available':
        query += " HAVING available_copies > 0"
    elif availability == 'borrowed':
        query += " HAVING available_copies = 0 AND total_copies > 0"

    # Sorting
    if sort_by == 'title_desc':
        query += " ORDER BY b.title DESC"
    elif sort_by == 'year_desc':
        query += " ORDER BY b.year_ DESC NULLS LAST"
    elif sort_by == 'year_asc':
        query += " ORDER BY b.year_ ASC NULLS LAST"
    elif sort_by == 'copies_desc':
        query += " ORDER BY total_copies DESC"
    else:
        query += " ORDER BY b.title ASC"

    rows = [dict(r) for r in c.execute(query, params).fetchall()]
    conn.close()
    return rows

def get_book_by_id(book_id):
    conn = get_db()
    c = conn.cursor()

    book = c.execute('''
        SELECT b.*, p.publisher_name, p.address as publisher_address, p.phone as publisher_phone,
               c.category_name
        FROM book b
        LEFT JOIN publisher p ON b.publisher_id = p.publisher_id
        LEFT JOIN category c ON b.category_id = c.category_id
        WHERE b.book_id = ?
    ''', (book_id,)).fetchone()

    if not book:
        conn.close()
        return None

    book_dict = dict(book)

    # Authors
    authors = [dict(r) for r in c.execute('''
        SELECT a.author_id, a.author_name, a.nationality
        FROM author a
        JOIN book_author ba ON a.author_id = ba.author_id
        WHERE ba.book_id = ?
    ''', (book_id,)).fetchall()]
    book_dict['authors'] = authors

    # Copies with shelf & managing librarian
    copies = [dict(r) for r in c.execute('''
        SELECT bc.copy_id, bc.status, s.shelf_id, s.floor, s.section,
               GROUP_CONCAT(l.name, ', ') AS managers,
               (SELECT m.name FROM borrow br 
                JOIN member m ON br.member_id = m.member_id 
                WHERE br.copy_id = bc.copy_id AND br.return_date IS NULL LIMIT 1) as current_borrower,
               (SELECT br.due_date FROM borrow br 
                WHERE br.copy_id = bc.copy_id AND br.return_date IS NULL LIMIT 1) as current_due_date
        FROM book_copy bc
        LEFT JOIN shelf s ON bc.shelf_id = s.shelf_id
        LEFT JOIN manages mg ON bc.copy_id = mg.copy_id
        LEFT JOIN librarian l ON mg.librarian_id = l.librarian_id
        WHERE bc.book_id = ?
        GROUP BY bc.copy_id
        ORDER BY bc.copy_id ASC
    ''', (book_id,)).fetchall()]
    book_dict['copies'] = copies

    # Borrow history for this book
    history = [dict(r) for r in c.execute('''
        SELECT br.borrow_id, br.copy_id, br.issue_date, br.due_date, br.return_date, br.fine_amount,
               m.member_id, m.name as member_name
        FROM borrow br
        JOIN book_copy bc ON br.copy_id = bc.copy_id
        JOIN member m ON br.member_id = m.member_id
        WHERE bc.book_id = ?
        ORDER BY br.issue_date DESC
        LIMIT 20
    ''', (book_id,)).fetchall()]
    book_dict['history'] = history

    conn.close()
    return book_dict

def add_book(title, isbn, edition, year, publisher_id, category_id, author_ids, copy_count=1, shelf_id=None, librarian_id=None):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO book (title, ISBN, edition, year_, publisher_id, category_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (title.strip(), isbn.strip() if isbn else None, edition.strip() if edition else None,
          int(year) if year else None,
          int(publisher_id) if publisher_id else None,
          int(category_id) if category_id else None))
    book_id = c.lastrowid

    if author_ids:
        for aid in author_ids:
            if aid:
                c.execute("INSERT OR IGNORE INTO book_author (book_id, author_id) VALUES (?, ?)", (book_id, int(aid)))

    # Initial copies
    copy_count = max(0, int(copy_count or 0))
    for _ in range(copy_count):
        c.execute('''
            INSERT INTO book_copy (book_id, shelf_id, status)
            VALUES (?, ?, 'Available')
        ''', (book_id, int(shelf_id) if shelf_id else None))
        cid = c.lastrowid
        if librarian_id:
            c.execute("INSERT OR IGNORE INTO manages (librarian_id, copy_id) VALUES (?, ?)", (int(librarian_id), cid))

    conn.commit()
    conn.close()
    return book_id

def update_book(book_id, title, isbn, edition, year, publisher_id, category_id, author_ids):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE book
        SET title = ?, ISBN = ?, edition = ?, year_ = ?, publisher_id = ?, category_id = ?
        WHERE book_id = ?
    ''', (title.strip(), isbn.strip() if isbn else None, edition.strip() if edition else None,
          int(year) if year else None,
          int(publisher_id) if publisher_id else None,
          int(category_id) if category_id else None,
          int(book_id)))

    c.execute("DELETE FROM book_author WHERE book_id = ?", (book_id,))
    if author_ids:
        for aid in author_ids:
            if aid:
                c.execute("INSERT OR IGNORE INTO book_author (book_id, author_id) VALUES (?, ?)", (book_id, int(aid)))

    conn.commit()
    conn.close()

def delete_book(book_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM book WHERE book_id = ?", (book_id,))
    conn.commit()
    conn.close()

# ----------------- COPIES & SHELVES & MANAGES -----------------

def get_available_copies():
    conn = get_db()
    c = conn.cursor()
    rows = [dict(r) for r in c.execute('''
        SELECT bc.copy_id, bc.status, b.title, b.book_id, s.floor, s.section
        FROM book_copy bc
        JOIN book b ON bc.book_id = b.book_id
        LEFT JOIN shelf s ON bc.shelf_id = s.shelf_id
        WHERE bc.status = 'Available'
        ORDER BY b.title ASC, bc.copy_id ASC
    ''').fetchall()]
    conn.close()
    return rows

def get_all_copies(shelf_id=None):
    conn = get_db()
    c = conn.cursor()
    query = '''
        SELECT bc.copy_id, bc.status, b.book_id, b.title, b.ISBN,
               s.shelf_id, s.floor, s.section,
               GROUP_CONCAT(l.name, ', ') AS managers,
               GROUP_CONCAT(l.librarian_id, ',') AS manager_ids
        FROM book_copy bc
        JOIN book b ON bc.book_id = b.book_id
        LEFT JOIN shelf s ON bc.shelf_id = s.shelf_id
        LEFT JOIN manages mg ON bc.copy_id = mg.copy_id
        LEFT JOIN librarian l ON mg.librarian_id = l.librarian_id
    '''
    params = []
    if shelf_id:
        query += " WHERE bc.shelf_id = ?"
        params.append(shelf_id)

    query += " GROUP BY bc.copy_id ORDER BY bc.copy_id DESC"
    rows = [dict(r) for r in c.execute(query, params).fetchall()]
    conn.close()
    return rows

def add_copy(book_id, shelf_id, status='Available', librarian_id=None):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO book_copy (book_id, shelf_id, status)
        VALUES (?, ?, ?)
    ''', (int(book_id), int(shelf_id) if shelf_id else None, status))
    copy_id = c.lastrowid
    if librarian_id:
        c.execute("INSERT OR IGNORE INTO manages (librarian_id, copy_id) VALUES (?, ?)", (int(librarian_id), copy_id))
    conn.commit()
    conn.close()
    return copy_id

def update_copy(copy_id, shelf_id, status, librarian_ids=None):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE book_copy
        SET shelf_id = ?, status = ?
        WHERE copy_id = ?
    ''', (int(shelf_id) if shelf_id else None, status, int(copy_id)))

    if librarian_ids is not None:
        c.execute("DELETE FROM manages WHERE copy_id = ?", (copy_id,))
        for lid in librarian_ids:
            if lid:
                c.execute("INSERT OR IGNORE INTO manages (librarian_id, copy_id) VALUES (?, ?)", (int(lid), copy_id))

    conn.commit()
    conn.close()

def delete_copy(copy_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM book_copy WHERE copy_id = ?", (copy_id,))
    conn.commit()
    conn.close()

# ----------------- BORROW / CIRCULATION -----------------

def get_borrows(status_filter='all'):
    conn = get_db()
    c = conn.cursor()
    today_str = datetime.now().date().isoformat()

    query = '''
        SELECT br.borrow_id, br.issue_date, br.due_date, br.return_date, br.fine_amount,
               m.member_id, m.name as member_name, m.phone as member_phone, m.email as member_email,
               bc.copy_id, bc.status as copy_status,
               bk.book_id, bk.title as book_title, bk.ISBN,
               s.floor, s.section
        FROM borrow br
        JOIN member m ON br.member_id = m.member_id
        JOIN book_copy bc ON br.copy_id = bc.copy_id
        JOIN book bk ON bc.book_id = bk.book_id
        LEFT JOIN shelf s ON bc.shelf_id = s.shelf_id
        WHERE 1=1
    '''

    if status_filter == 'active':
        query += " AND br.return_date IS NULL"
    elif status_filter == 'overdue':
        query += f" AND br.return_date IS NULL AND br.due_date < '{today_str}'"
    elif status_filter == 'returned':
        query += " AND br.return_date IS NOT NULL"

    query += " ORDER BY CASE WHEN br.return_date IS NULL THEN 0 ELSE 1 END, br.due_date ASC, br.borrow_id DESC"
    rows = [dict(r) for r in c.execute(query).fetchall()]

    # Annotate overdue status dynamically (₹5 per day late in INR)
    today = datetime.now().date()
    for row in rows:
        due = datetime.strptime(row['due_date'], "%Y-%m-%d").date()
        if not row['return_date']:
            if due < today:
                days_over = (today - due).days
                row['is_overdue'] = True
                row['days_overdue'] = days_over
                est_fine = days_over * 5.0
                row['est_fine'] = max(est_fine, float(row['fine_amount'] or 0.0))
            else:
                row['is_overdue'] = False
                row['days_overdue'] = 0
                row['est_fine'] = 0.0
        else:
            ret = datetime.strptime(row['return_date'], "%Y-%m-%d").date()
            row['is_overdue'] = False
            row['days_overdue'] = max(0, (ret - due).days)
            row['est_fine'] = float(row['fine_amount'] or 0.0)

    conn.close()
    return rows

def issue_book(member_id, copy_id, issue_date=None, due_date=None):
    conn = get_db()
    c = conn.cursor()

    if not issue_date:
        issue_date = datetime.now().date().isoformat()
    if not due_date:
        due_date = (datetime.now().date() + timedelta(days=14)).isoformat()

    c.execute('''
        INSERT INTO borrow (member_id, copy_id, issue_date, due_date, return_date, fine_amount)
        VALUES (?, ?, ?, ?, NULL, 0.00)
    ''', (int(member_id), int(copy_id), issue_date, due_date))

    # Mark copy as borrowed
    c.execute("UPDATE book_copy SET status = 'Borrowed' WHERE copy_id = ?", (int(copy_id),))

    conn.commit()
    conn.close()

def return_book(borrow_id, return_date=None, fine_amount=0.0):
    conn = get_db()
    c = conn.cursor()

    borrow = c.execute("SELECT copy_id, due_date FROM borrow WHERE borrow_id = ?", (borrow_id,)).fetchone()
    if not borrow:
        conn.close()
        return False

    copy_id = borrow['copy_id']
    due_date_str = borrow['due_date']

    if not return_date:
        return_date = datetime.now().date().isoformat()

    # Calculate fine automatically if fine_amount is 0 and it's late (₹5 per day late)
    if fine_amount is None or float(fine_amount) == 0.0:
        ret = datetime.strptime(return_date, "%Y-%m-%d").date()
        due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        if ret > due:
            fine_amount = (ret - due).days * 5.0
        else:
            fine_amount = 0.0

    c.execute('''
        UPDATE borrow
        SET return_date = ?, fine_amount = ?
        WHERE borrow_id = ?
    ''', (return_date, float(fine_amount), int(borrow_id)))

    # Mark copy back as Available
    c.execute("UPDATE book_copy SET status = 'Available' WHERE copy_id = ?", (copy_id,))

    conn.commit()
    conn.close()
    return True

def delete_borrow(borrow_id):
    conn = get_db()
    c = conn.cursor()
    b = c.execute("SELECT copy_id, return_date FROM borrow WHERE borrow_id = ?", (borrow_id,)).fetchone()
    if b:
        # If it was active, reset copy status to Available
        if not b['return_date']:
            c.execute("UPDATE book_copy SET status = 'Available' WHERE copy_id = ?", (b['copy_id'],))
        c.execute("DELETE FROM borrow WHERE borrow_id = ?", (borrow_id,))
    conn.commit()
    conn.close()

# ----------------- MEMBERS -----------------

def get_members(search=None):
    conn = get_db()
    c = conn.cursor()
    query = '''
        SELECT m.*,
               COUNT(DISTINCT CASE WHEN br.return_date IS NULL THEN br.borrow_id END) AS active_borrows,
               COUNT(DISTINCT br.borrow_id) AS total_borrows,
               COALESCE(SUM(br.fine_amount), 0.0) AS total_fines
        FROM member m
        LEFT JOIN borrow br ON m.member_id = br.member_id
        WHERE 1=1
    '''
    params = []
    if search:
        search_param = f"%{search.strip()}%"
        query += " AND (m.name LIKE ? OR m.email LIKE ? OR m.phone LIKE ? OR m.address LIKE ?)"
        params.extend([search_param, search_param, search_param, search_param])

    query += " GROUP BY m.member_id ORDER BY m.name ASC"
    rows = [dict(r) for r in c.execute(query, params).fetchall()]
    conn.close()
    return rows

def get_member_detail(member_id):
    conn = get_db()
    c = conn.cursor()
    member = c.execute("SELECT * FROM member WHERE member_id = ?", (member_id,)).fetchone()
    if not member:
        conn.close()
        return None

    member_dict = dict(member)
    borrows = [dict(r) for r in c.execute('''
        SELECT br.borrow_id, br.issue_date, br.due_date, br.return_date, br.fine_amount,
               bc.copy_id, bk.book_id, bk.title as book_title
        FROM borrow br
        JOIN book_copy bc ON br.copy_id = bc.copy_id
        JOIN book bk ON bc.book_id = bk.book_id
        WHERE br.member_id = ?
        ORDER BY br.issue_date DESC
    ''', (member_id,)).fetchall()]
    member_dict['borrows'] = borrows
    conn.close()
    return member_dict

def add_member(name, address, phone, email, membership_date=None):
    conn = get_db()
    c = conn.cursor()
    if not membership_date:
        membership_date = datetime.now().date().isoformat()
    c.execute('''
        INSERT INTO member (name, address, phone, email, membership_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (name.strip(), address.strip() if address else None, phone.strip() if phone else None,
          email.strip() if email else None, membership_date))
    mid = c.lastrowid
    conn.commit()
    conn.close()
    return mid

def update_member(member_id, name, address, phone, email, membership_date):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE member
        SET name = ?, address = ?, phone = ?, email = ?, membership_date = ?
        WHERE member_id = ?
    ''', (name.strip(), address.strip() if address else None, phone.strip() if phone else None,
          email.strip() if email else None, membership_date, int(member_id)))
    conn.commit()
    conn.close()

def delete_member(member_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM member WHERE member_id = ?", (member_id,))
    conn.commit()
    conn.close()

# ----------------- LIBRARIANS & MANAGES -----------------

def get_librarians():
    conn = get_db()
    c = conn.cursor()
    rows = [dict(r) for r in c.execute('''
        SELECT l.*, COUNT(DISTINCT mg.copy_id) AS managed_copies_count
        FROM librarian l
        LEFT JOIN manages mg ON l.librarian_id = mg.librarian_id
        GROUP BY l.librarian_id
        ORDER BY l.name ASC
    ''').fetchall()]
    conn.close()
    return rows

def get_librarian_detail(librarian_id):
    conn = get_db()
    c = conn.cursor()
    lib = c.execute("SELECT * FROM librarian WHERE librarian_id = ?", (librarian_id,)).fetchone()
    if not lib:
        conn.close()
        return None
    lib_dict = dict(lib)
    copies = [dict(r) for r in c.execute('''
        SELECT bc.copy_id, bc.status, bk.title, s.floor, s.section
        FROM manages mg
        JOIN book_copy bc ON mg.copy_id = bc.copy_id
        JOIN book bk ON bc.book_id = bk.book_id
        LEFT JOIN shelf s ON bc.shelf_id = s.shelf_id
        WHERE mg.librarian_id = ?
        ORDER BY bk.title ASC
    ''', (librarian_id,)).fetchall()]
    lib_dict['managed_copies'] = copies
    conn.close()
    return lib_dict

def add_librarian(name, phone, email):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO librarian (name, phone, email)
        VALUES (?, ?, ?)
    ''', (name.strip(), phone.strip() if phone else None, email.strip() if email else None))
    lid = c.lastrowid
    conn.commit()
    conn.close()
    return lid

def update_librarian(librarian_id, name, phone, email):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE librarian
        SET name = ?, phone = ?, email = ?
        WHERE librarian_id = ?
    ''', (name.strip(), phone.strip() if phone else None, email.strip() if email else None, int(librarian_id)))
    conn.commit()
    conn.close()

def delete_librarian(librarian_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM librarian WHERE librarian_id = ?", (librarian_id,))
    conn.commit()
    conn.close()

def assign_librarian_copies(librarian_id, copy_ids):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM manages WHERE librarian_id = ?", (librarian_id,))
    for cid in copy_ids:
        if cid:
            c.execute("INSERT OR IGNORE INTO manages (librarian_id, copy_id) VALUES (?, ?)", (librarian_id, int(cid)))
    conn.commit()
    conn.close()

# ----------------- SHELVES -----------------

def get_shelves():
    conn = get_db()
    c = conn.cursor()
    rows = [dict(r) for r in c.execute('''
        SELECT s.*,
               COUNT(DISTINCT bc.copy_id) AS total_copies,
               COUNT(DISTINCT CASE WHEN bc.status = 'Available' THEN bc.copy_id END) AS available_copies
        FROM shelf s
        LEFT JOIN book_copy bc ON s.shelf_id = bc.shelf_id
        GROUP BY s.shelf_id
        ORDER BY s.floor ASC, s.section ASC
    ''').fetchall()]
    conn.close()
    return rows

def add_shelf(floor, section):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO shelf (floor, section) VALUES (?, ?)", (floor.strip(), section.strip()))
    sid = c.lastrowid
    conn.commit()
    conn.close()
    return sid

def update_shelf(shelf_id, floor, section):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE shelf SET floor = ?, section = ? WHERE shelf_id = ?", (floor.strip(), section.strip(), int(shelf_id)))
    conn.commit()
    conn.close()

def delete_shelf(shelf_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM shelf WHERE shelf_id = ?", (shelf_id,))
    conn.commit()
    conn.close()

# ----------------- AUTHORS, PUBLISHERS, CATEGORIES -----------------

def get_authors():
    conn = get_db()
    c = conn.cursor()
    rows = [dict(r) for r in c.execute('''
        SELECT a.*, COUNT(DISTINCT ba.book_id) AS books_count
        FROM author a
        LEFT JOIN book_author ba ON a.author_id = ba.author_id
        GROUP BY a.author_id
        ORDER BY a.author_name ASC
    ''').fetchall()]
    conn.close()
    return rows

def add_author(name, nationality):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO author (author_name, nationality) VALUES (?, ?)", (name.strip(), nationality.strip() if nationality else None))
    aid = c.lastrowid
    conn.commit()
    conn.close()
    return aid

def update_author(author_id, name, nationality):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE author SET author_name = ?, nationality = ? WHERE author_id = ?", (name.strip(), nationality.strip() if nationality else None, int(author_id)))
    conn.commit()
    conn.close()

def delete_author(author_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM author WHERE author_id = ?", (author_id,))
    conn.commit()
    conn.close()

def get_publishers():
    conn = get_db()
    c = conn.cursor()
    rows = [dict(r) for r in c.execute('''
        SELECT p.*, COUNT(DISTINCT b.book_id) AS books_count
        FROM publisher p
        LEFT JOIN book b ON p.publisher_id = b.publisher_id
        GROUP BY p.publisher_id
        ORDER BY p.publisher_name ASC
    ''').fetchall()]
    conn.close()
    return rows

def add_publisher(name, address, phone):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO publisher (publisher_name, address, phone) VALUES (?, ?, ?)",
              (name.strip(), address.strip() if address else None, phone.strip() if phone else None))
    pid = c.lastrowid
    conn.commit()
    conn.close()
    return pid

def update_publisher(publisher_id, name, address, phone):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE publisher SET publisher_name = ?, address = ?, phone = ? WHERE publisher_id = ?",
              (name.strip(), address.strip() if address else None, phone.strip() if phone else None, int(publisher_id)))
    conn.commit()
    conn.close()

def delete_publisher(publisher_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM publisher WHERE publisher_id = ?", (publisher_id,))
    conn.commit()
    conn.close()

def get_categories():
    conn = get_db()
    c = conn.cursor()
    rows = [dict(r) for r in c.execute('''
        SELECT c.*, COUNT(DISTINCT b.book_id) AS books_count
        FROM category c
        LEFT JOIN book b ON c.category_id = b.category_id
        GROUP BY c.category_id
        ORDER BY c.category_name ASC
    ''').fetchall()]
    conn.close()
    return rows

def add_category(name):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO category (category_name) VALUES (?)", (name.strip(),))
    cid = c.lastrowid
    conn.commit()
    conn.close()
    return cid

def update_category(category_id, name):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE category SET category_name = ? WHERE category_id = ?", (name.strip(), int(category_id)))
    conn.commit()
    conn.close()

def delete_category(category_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM category WHERE category_id = ?", (category_id,))
    conn.commit()
    conn.close()

# ----------------- SCHEMA & SQL RUNNER -----------------

def get_schema_metadata():
    conn = get_db()
    c = conn.cursor()

    tables = [
        'member', 'librarian', 'publisher', 'category', 'book',
        'author', 'book_author', 'shelf', 'book_copy', 'borrow', 'manages'
    ]

    schema_info = {}
    for tbl in tables:
        cols = [dict(r) for r in c.execute(f"PRAGMA table_info({tbl})").fetchall()]
        fks = [dict(r) for r in c.execute(f"PRAGMA foreign_key_list({tbl})").fetchall()]
        count = c.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        schema_info[tbl] = {
            'columns': cols,
            'foreign_keys': fks,
            'row_count': count
        }
    conn.close()
    return schema_info

def execute_custom_query(sql):
    conn = get_db()
    c = conn.cursor()
    sql_stripped = sql.strip().upper()
    if not sql_stripped.startswith("SELECT") and not sql_stripped.startswith("WITH") and not sql_stripped.startswith("EXPLAIN"):
        conn.close()
        return {"error": "Only SELECT or read-only queries are supported in the SQL Query Runner."}

    try:
        cursor = c.execute(sql)
        headers = [d[0] for d in cursor.description] if cursor.description else []
        rows = [list(r) for r in cursor.fetchall()]
        conn.close()
        return {"headers": headers, "rows": rows, "count": len(rows)}
    except Exception as e:
        conn.close()
        return {"error": str(e)}

if __name__ == '__main__':
    init_db(reset=True)
    seed_sample_data(force=True)
    print("Database re-initialized and seeded with rich Indian library catalog data!")
