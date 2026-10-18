import unittest
from app import app
import database as db

class LibraryAppTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_routes_status(self):
        routes = [
            '/',
            '/catalog',
            '/catalog/1',
            '/circulation',
            '/members',
            '/members/1',
            '/librarians',
            '/librarians/1',
            '/inventory',
            '/metadata',
            '/metadata?tab=publishers',
            '/metadata?tab=authors',
            '/schema'
        ]
        for route in routes:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} failed with status {resp.status_code}")
            print(f"Route {route} -> OK (200)")

    def test_sql_query_api(self):
        resp = self.client.post('/api/query', json={'query': 'SELECT COUNT(*) as count FROM book;'})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('headers', data)
        self.assertIn('rows', data)
        print("SQL API Test -> OK", data)

    def test_circulation_issue_and_return(self):
        import time
        # Add a temporary member
        mid = db.add_member("Test Patron", "123 Test St", "555-9999", "test@test.com")
        # Add a test book with 1 copy
        test_isbn = f"999-{int(time.time()*1000)}"
        bid = db.add_book("Test Automated Book", test_isbn, "1st", 2024, None, None, [], copy_count=1)
        avail = db.get_available_copies()
        test_copy = [c for c in avail if c['book_id'] == bid][0]

        # Issue copy
        db.issue_book(mid, test_copy['copy_id'], "2026-10-01", "2026-10-15")
        
        # Verify status is Borrowed
        book = db.get_book_by_id(bid)
        copy_status = [c['status'] for c in book['copies'] if c['copy_id'] == test_copy['copy_id']][0]
        self.assertEqual(copy_status, 'Borrowed')

        # Find borrow record
        borrows = db.get_borrows('active')
        b_rec = [b for b in borrows if b['copy_id'] == test_copy['copy_id']][0]

        # Return copy
        db.return_book(b_rec['borrow_id'], "2026-10-18", fine_amount=1.50)

        # Verify status is Available again
        book_after = db.get_book_by_id(bid)
        copy_status_after = [c['status'] for c in book_after['copies'] if c['copy_id'] == test_copy['copy_id']][0]
        self.assertEqual(copy_status_after, 'Available')
        
        # Cleanup test records
        db.delete_borrow(b_rec['borrow_id'])
        db.delete_book(bid)
        db.delete_member(mid)
        print("Circulation Issue & Return cycle -> OK")

if __name__ == '__main__':
    unittest.main()
