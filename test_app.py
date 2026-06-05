import unittest
import os
import tempfile
import io
import pandas as pd
from app import app, db, User, AnalysisHistory

class AppTestCase(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()

        # Create the database and the database tables
        with app.app_context():
            db.create_all()

    def tearDown(self):
        # Drop the database tables
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register(self):
        response = self.client.post('/register', data=dict(
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Akun berhasil dibuat!', response.data)

    def test_login(self):
        self.client.post('/register', data=dict(
            username='testuser',
            password='testpassword'
        ))
        response = self.client.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logout (testuser)', response.data)

    def test_analysis_history(self):
        # Setup user and login
        self.client.post('/register', data=dict(
            username='testuser',
            password='testpassword'
        ))
        self.client.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ))

        # Test file analysis
        data = {
            'text_column': 'text',
            'file': (io.BytesIO(b"text\nsaya sangat suka ini\nini jelek sekali"), 'test.csv')
        }

        response = self.client.post('/analysis', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Download Hasil Analisis', response.data)

        # Check history
        history_response = self.client.get('/history')
        self.assertEqual(history_response.status_code, 200)
        self.assertIn(b'test.csv', history_response.data)
        self.assertIn(b'Unduh Hasil', history_response.data)

if __name__ == '__main__':
    unittest.main()