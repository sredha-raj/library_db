import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import database as db

app = Flask(__name__)
app.secret_key = 'nalanda-indian-library-secret-key-2026'

# Initialize database on start
db.init_db(reset=False)
db.seed_sample_data(force=False)

# Custom template filters
@app.template_filter('format_date')
def format_date(value):
    if not value:
        return '—'
    try:
        dt = datetime.strptime(str(value), "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except Exception:
        return str(value)

@app.template_filter('currency')
def format_currency(value):
    try:
        val = float(value or 0.0)
        return f"₹{val:.2f}"
    except (ValueError, TypeError):
        return "₹0.00"

# ----------------- ROUTES -----------------

@app.route('/')
def dashboard():
    stats = db.get_dashboard_stats()
    categories = db.get_categories()
    members = db.get_members()
    available_copies = db.get_available_copies()
    return render_template('dashboard.html', stats=stats, categories=categories,
                           members=members, available_copies=available_copies)

@app.route('/catalog')
def catalog():
    search = request.args.get('q', '').strip()
    category_id = request.args.get('category', '').strip()
    category_id = int(category_id) if category_id.isdigit() else None
    availability = request.args.get('status', '').strip()
    sort_by = request.args.get('sort', 'title_asc').strip()

    books = db.get_books(search=search, category_id=category_id, availability=availability, sort_by=sort_by)
    categories = db.get_categories()
    publishers = db.get_publishers()
    authors = db.get_authors()
    shelves = db.get_shelves()
    librarians = db.get_librarians()

    return render_template('catalog.html', books=books, categories=categories,
                           publishers=publishers, authors=authors, shelves=shelves,
                           librarians=librarians, search=search, selected_cat=category_id,
                           selected_status=availability, selected_sort=sort_by)

@app.route('/catalog/<int:book_id>')
def book_detail(book_id):
    book = db.get_book_by_id(book_id)
    if not book:
        flash("Book not found.", "error")
        return redirect(url_for('catalog'))
    
    shelves = db.get_shelves()
    librarians = db.get_librarians()
    members = db.get_members()
    publishers = db.get_publishers()
    categories = db.get_categories()
    authors = db.get_authors()
    return render_template('book_detail.html', book=book, shelves=shelves,
                           librarians=librarians, members=members, publishers=publishers,
                           categories=categories, authors=authors)

@app.route('/catalog/add', methods=['POST'])
def add_book():
    try:
        title = request.form.get('title')
        isbn = request.form.get('isbn')
        edition = request.form.get('edition')
        year = request.form.get('year')
        publisher_id = request.form.get('publisher_id')
        category_id = request.form.get('category_id')
        author_ids = request.form.getlist('author_ids')
        copy_count = request.form.get('copy_count', 1)
        shelf_id = request.form.get('shelf_id')
        librarian_id = request.form.get('librarian_id')

        if not title:
            flash("Book title is required.", "error")
            return redirect(url_for('catalog'))

        book_id = db.add_book(
            title=title, isbn=isbn, edition=edition, year=year,
            publisher_id=publisher_id, category_id=category_id,
            author_ids=author_ids, copy_count=copy_count,
            shelf_id=shelf_id, librarian_id=librarian_id
        )
        flash(f"Book '{title}' registered successfully with {copy_count} initial copy(s)!", "success")
        return redirect(url_for('book_detail', book_id=book_id))
    except Exception as e:
        flash(f"Failed to add book: {str(e)}", "error")
        return redirect(url_for('catalog'))

@app.route('/catalog/<int:book_id>/edit', methods=['POST'])
def edit_book(book_id):
    try:
        title = request.form.get('title')
        isbn = request.form.get('isbn')
        edition = request.form.get('edition')
        year = request.form.get('year')
        publisher_id = request.form.get('publisher_id')
        category_id = request.form.get('category_id')
        author_ids = request.form.getlist('author_ids')

        db.update_book(book_id, title, isbn, edition, year, publisher_id, category_id, author_ids)
        flash(f"Book '{title}' updated successfully!", "success")
    except Exception as e:
        flash(f"Failed to update book: {str(e)}", "error")
    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/catalog/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    try:
        db.delete_book(book_id)
        flash("Book and associated physical copies deleted successfully.", "success")
    except Exception as e:
        flash(f"Failed to delete book: {str(e)}", "error")
    return redirect(url_for('catalog'))

# ----------------- CIRCULATION (BORROW & RETURN & DELETE) -----------------

@app.route('/circulation')
def circulation():
    status = request.args.get('status', 'all')
    borrows = db.get_borrows(status_filter=status)
    members = db.get_members()
    available_copies = db.get_available_copies()
    today_str = datetime.now().date().isoformat()
    default_due = (datetime.now().date() + timedelta(days=14)).isoformat()

    return render_template('circulation.html', borrows=borrows, members=members,
                           available_copies=available_copies, current_status=status,
                           today_str=today_str, default_due=default_due)

@app.route('/circulation/issue', methods=['POST'])
def issue_book():
    try:
        member_id = request.form.get('member_id')
        copy_id = request.form.get('copy_id')
        issue_date = request.form.get('issue_date')
        due_date = request.form.get('due_date')

        if not member_id or not copy_id or not due_date:
            flash("Member, Book Copy, and Due Date are required.", "error")
            return redirect(url_for('circulation'))

        db.issue_book(member_id, copy_id, issue_date, due_date)
        flash(f"Book copy #{copy_id} successfully issued!", "success")
    except Exception as e:
        flash(f"Failed to issue book: {str(e)}", "error")
    return redirect(url_for('circulation'))

@app.route('/circulation/return', methods=['POST'])
def return_book():
    try:
        borrow_id = request.form.get('borrow_id')
        return_date = request.form.get('return_date') or datetime.now().date().isoformat()
        fine_amount = request.form.get('fine_amount')
        fine_amount = float(fine_amount) if fine_amount else 0.0

        db.return_book(borrow_id, return_date, fine_amount)
        flash(f"Borrow #{borrow_id} recorded as returned! Fine: ₹{fine_amount:.2f}", "success")
    except Exception as e:
        flash(f"Failed to return book: {str(e)}", "error")
    return redirect(url_for('circulation'))

@app.route('/circulation/<int:borrow_id>/delete', methods=['POST'])
def delete_borrow(borrow_id):
    try:
        db.delete_borrow(borrow_id)
        flash(f"Borrow record #{borrow_id} deleted successfully.", "success")
    except Exception as e:
        flash(f"Failed to delete borrow record: {str(e)}", "error")
    return redirect(url_for('circulation'))

# ----------------- COPIES, SHELVES & MANAGES -----------------

@app.route('/inventory')
def inventory():
    shelf_id = request.args.get('shelf_id', '').strip()
    shelf_id = int(shelf_id) if shelf_id.isdigit() else None

    shelves = db.get_shelves()
    copies = db.get_all_copies(shelf_id=shelf_id)
    books = db.get_books()
    librarians = db.get_librarians()

    return render_template('inventory.html', shelves=shelves, copies=copies,
                           books=books, librarians=librarians, selected_shelf=shelf_id)

@app.route('/inventory/copy/add', methods=['POST'])
def add_copy():
    try:
        book_id = request.form.get('book_id')
        shelf_id = request.form.get('shelf_id')
        status = request.form.get('status', 'Available')
        librarian_id = request.form.get('librarian_id')

        if not book_id:
            flash("Book selection is required.", "error")
            return redirect(url_for('inventory'))

        db.add_copy(book_id, shelf_id, status, librarian_id)
        flash("New physical book copy added to inventory successfully!", "success")
    except Exception as e:
        flash(f"Failed to add copy: {str(e)}", "error")
    
    redirect_to = request.form.get('redirect_to')
    if redirect_to == 'book_detail':
        return redirect(url_for('book_detail', book_id=request.form.get('book_id')))
    return redirect(url_for('inventory'))

@app.route('/inventory/copy/<int:copy_id>/edit', methods=['POST'])
def edit_copy(copy_id):
    try:
        shelf_id = request.form.get('shelf_id')
        status = request.form.get('status', 'Available')
        librarian_ids = request.form.getlist('librarian_ids')

        db.update_copy(copy_id, shelf_id, status, librarian_ids)
        flash(f"Copy #{copy_id} updated successfully!", "success")
    except Exception as e:
        flash(f"Failed to update copy #{copy_id}: {str(e)}", "error")

    redirect_to = request.form.get('redirect_to')
    book_id = request.form.get('book_id')
    if redirect_to == 'book_detail' and book_id:
        return redirect(url_for('book_detail', book_id=book_id))
    return redirect(url_for('inventory'))

@app.route('/inventory/copy/<int:copy_id>/delete', methods=['POST'])
def delete_copy(copy_id):
    try:
        db.delete_copy(copy_id)
        flash(f"Copy #{copy_id} deleted successfully.", "success")
    except Exception as e:
        flash(f"Failed to delete copy #{copy_id}: {str(e)}", "error")

    redirect_to = request.form.get('redirect_to')
    book_id = request.form.get('book_id')
    if redirect_to == 'book_detail' and book_id:
        return redirect(url_for('book_detail', book_id=book_id))
    return redirect(url_for('inventory'))

@app.route('/inventory/shelf/add', methods=['POST'])
def add_shelf():
    try:
        floor = request.form.get('floor')
        section = request.form.get('section')
        if not floor or not section:
            flash("Floor and Section are required.", "error")
            return redirect(url_for('inventory'))

        db.add_shelf(floor, section)
        flash(f"Shelf ({floor} - {section}) created successfully!", "success")
    except Exception as e:
        flash(f"Failed to create shelf: {str(e)}", "error")
    return redirect(url_for('inventory'))

@app.route('/inventory/shelf/<int:shelf_id>/edit', methods=['POST'])
def edit_shelf(shelf_id):
    try:
        floor = request.form.get('floor')
        section = request.form.get('section')
        db.update_shelf(shelf_id, floor, section)
        flash(f"Shelf #{shelf_id} updated successfully.", "success")
    except Exception as e:
        flash(f"Failed to update shelf: {str(e)}", "error")
    return redirect(url_for('inventory'))

@app.route('/inventory/shelf/<int:shelf_id>/delete', methods=['POST'])
def delete_shelf(shelf_id):
    try:
        db.delete_shelf(shelf_id)
        flash(f"Shelf #{shelf_id} deleted.", "success")
    except Exception as e:
        flash(f"Failed to delete shelf: {str(e)}", "error")
    return redirect(url_for('inventory'))

# ----------------- MEMBERS -----------------

@app.route('/members')
def members():
    search = request.args.get('q', '').strip()
    member_list = db.get_members(search=search)
    return render_template('members.html', members=member_list, search=search)

@app.route('/members/<int:member_id>')
def member_detail(member_id):
    member = db.get_member_detail(member_id)
    if not member:
        flash("Member not found.", "error")
        return redirect(url_for('members'))
    return render_template('member_detail.html', member=member)

@app.route('/members/add', methods=['POST'])
def add_member():
    try:
        name = request.form.get('name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        email = request.form.get('email')
        membership_date = request.form.get('membership_date') or datetime.now().date().isoformat()

        if not name:
            flash("Member name is required.", "error")
            return redirect(url_for('members'))

        mid = db.add_member(name, address, phone, email, membership_date)
        flash(f"Member '{name}' registered successfully!", "success")
        return redirect(url_for('member_detail', member_id=mid))
    except Exception as e:
        flash(f"Failed to add member: {str(e)}", "error")
        return redirect(url_for('members'))

@app.route('/members/<int:member_id>/edit', methods=['POST'])
def edit_member(member_id):
    try:
        name = request.form.get('name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        email = request.form.get('email')
        membership_date = request.form.get('membership_date')

        db.update_member(member_id, name, address, phone, email, membership_date)
        flash(f"Member details updated.", "success")
    except Exception as e:
        flash(f"Failed to update member: {str(e)}", "error")
    return redirect(url_for('member_detail', member_id=member_id))

@app.route('/members/<int:member_id>/delete', methods=['POST'])
def delete_member(member_id):
    try:
        db.delete_member(member_id)
        flash("Member deleted successfully.", "success")
    except Exception as e:
        flash(f"Failed to delete member: {str(e)}", "error")
    return redirect(url_for('members'))

# ----------------- LIBRARIANS -----------------

@app.route('/librarians')
def librarians():
    lib_list = db.get_librarians()
    all_copies = db.get_all_copies()
    return render_template('librarians.html', librarians=lib_list, all_copies=all_copies)

@app.route('/librarians/<int:librarian_id>')
def librarian_detail(librarian_id):
    lib = db.get_librarian_detail(librarian_id)
    if not lib:
        flash("Librarian not found.", "error")
        return redirect(url_for('librarians'))
    all_copies = db.get_all_copies()
    return render_template('librarian_detail.html', librarian=lib, all_copies=all_copies)

@app.route('/librarians/add', methods=['POST'])
def add_librarian():
    try:
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')

        if not name:
            flash("Librarian name is required.", "error")
            return redirect(url_for('librarians'))

        lid = db.add_librarian(name, phone, email)
        flash(f"Librarian '{name}' added successfully!", "success")
        return redirect(url_for('librarian_detail', librarian_id=lid))
    except Exception as e:
        flash(f"Failed to add librarian: {str(e)}", "error")
        return redirect(url_for('librarians'))

@app.route('/librarians/<int:librarian_id>/edit', methods=['POST'])
def edit_librarian(librarian_id):
    try:
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')

        db.update_librarian(librarian_id, name, phone, email)
        flash("Librarian updated successfully.", "success")
    except Exception as e:
        flash(f"Failed to update librarian: {str(e)}", "error")
    return redirect(url_for('librarian_detail', librarian_id=librarian_id))

@app.route('/librarians/<int:librarian_id>/assign', methods=['POST'])
def assign_librarian(librarian_id):
    try:
        copy_ids = request.form.getlist('copy_ids')
        db.assign_librarian_copies(librarian_id, copy_ids)
        flash("Managed copy assignments updated in manages table!", "success")
    except Exception as e:
        flash(f"Failed to assign copies: {str(e)}", "error")
    return redirect(url_for('librarian_detail', librarian_id=librarian_id))

@app.route('/librarians/<int:librarian_id>/delete', methods=['POST'])
def delete_librarian(librarian_id):
    try:
        db.delete_librarian(librarian_id)
        flash("Librarian deleted.", "success")
    except Exception as e:
        flash(f"Failed to delete librarian: {str(e)}", "error")
    return redirect(url_for('librarians'))

# ----------------- METADATA (PUBLISHERS, CATEGORIES, AUTHORS) -----------------

@app.route('/metadata')
def metadata():
    tab = request.args.get('tab', 'categories')
    categories = db.get_categories()
    publishers = db.get_publishers()
    authors = db.get_authors()
    return render_template('metadata.html', tab=tab, categories=categories,
                           publishers=publishers, authors=authors)

@app.route('/metadata/category/add', methods=['POST'])
def add_category():
    try:
        name = request.form.get('category_name')
        if name:
            db.add_category(name)
            flash(f"Category '{name}' created.", "success")
    except Exception as e:
        flash(f"Failed to add category: {str(e)}", "error")
    return redirect(url_for('metadata', tab='categories'))

@app.route('/metadata/category/<int:category_id>/edit', methods=['POST'])
def edit_category(category_id):
    try:
        name = request.form.get('category_name')
        if name:
            db.update_category(category_id, name)
            flash("Category updated successfully.", "success")
    except Exception as e:
        flash(f"Failed to update category: {str(e)}", "error")
    return redirect(url_for('metadata', tab='categories'))

@app.route('/metadata/category/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    try:
        db.delete_category(category_id)
        flash("Category deleted.", "success")
    except Exception as e:
        flash(f"Failed to delete category: {str(e)}", "error")
    return redirect(url_for('metadata', tab='categories'))

@app.route('/metadata/publisher/add', methods=['POST'])
def add_publisher():
    try:
        name = request.form.get('publisher_name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        if name:
            db.add_publisher(name, address, phone)
            flash(f"Publisher '{name}' added.", "success")
    except Exception as e:
        flash(f"Failed to add publisher: {str(e)}", "error")
    return redirect(url_for('metadata', tab='publishers'))

@app.route('/metadata/publisher/<int:publisher_id>/edit', methods=['POST'])
def edit_publisher(publisher_id):
    try:
        name = request.form.get('publisher_name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        if name:
            db.update_publisher(publisher_id, name, address, phone)
            flash("Publisher updated successfully.", "success")
    except Exception as e:
        flash(f"Failed to update publisher: {str(e)}", "error")
    return redirect(url_for('metadata', tab='publishers'))

@app.route('/metadata/publisher/<int:publisher_id>/delete', methods=['POST'])
def delete_publisher(publisher_id):
    try:
        db.delete_publisher(publisher_id)
        flash("Publisher deleted.", "success")
    except Exception as e:
        flash(f"Failed to delete publisher: {str(e)}", "error")
    return redirect(url_for('metadata', tab='publishers'))

@app.route('/metadata/author/add', methods=['POST'])
def add_author():
    try:
        name = request.form.get('author_name')
        nationality = request.form.get('nationality')
        if name:
            db.add_author(name, nationality)
            flash(f"Author '{name}' added.", "success")
    except Exception as e:
        flash(f"Failed to add author: {str(e)}", "error")
    return redirect(url_for('metadata', tab='authors'))

@app.route('/metadata/author/<int:author_id>/edit', methods=['POST'])
def edit_author(author_id):
    try:
        name = request.form.get('author_name')
        nationality = request.form.get('nationality')
        if name:
            db.update_author(author_id, name, nationality)
            flash("Author updated successfully.", "success")
    except Exception as e:
        flash(f"Failed to update author: {str(e)}", "error")
    return redirect(url_for('metadata', tab='authors'))

@app.route('/metadata/author/<int:author_id>/delete', methods=['POST'])
def delete_author(author_id):
    try:
        db.delete_author(author_id)
        flash("Author deleted.", "success")
    except Exception as e:
        flash(f"Failed to delete author: {str(e)}", "error")
    return redirect(url_for('metadata', tab='authors'))

# ----------------- SCHEMA & SQL EXPLORER -----------------

@app.route('/schema')
def schema():
    schema_info = db.get_schema_metadata()
    return render_template('schema.html', schema_info=schema_info)

@app.route('/api/query', methods=['POST'])
def run_query():
    data = request.get_json() or {}
    sql = data.get('query', '')
    result = db.execute_custom_query(sql)
    return jsonify(result)

@app.route('/api/reset-demo', methods=['POST'])
def reset_demo():
    try:
        db.init_db(reset=True)
        db.seed_sample_data(force=True)
        return jsonify({"success": True, "message": "Database reset and seeded with rich Indian library demo data!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5555, host='127.0.0.1')
