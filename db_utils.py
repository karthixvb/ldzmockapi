import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
from bson.objectid import ObjectId

class DatabaseManager:
    def __init__(self):
        self.mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
        self.db_name = os.getenv('MONGODB_DB_NAME', 'mockup_db')
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            # Test connection
            self.client.admin.command('ping')
            print("Connected to MongoDB successfully")
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

    def create_template(self, template_data):
        """Create a new template"""
        template_data['createdAt'] = datetime.utcnow()
        template_data['updatedAt'] = datetime.utcnow()
        result = self.db.templates.insert_one(template_data)
        return str(result.inserted_id)

    def get_template(self, template_id):
        """Get a template by ID"""
        try:
            return self.db.templates.find_one({'_id': ObjectId(template_id)})
        except:
            return None

    def get_all_templates(self, page=1, limit=10):
        """Get all templates with pagination"""
        skip = (page - 1) * limit
        templates = list(self.db.templates.find().skip(skip).limit(limit))
        total = self.db.templates.count_documents({})
        return templates, total

    def update_template(self, template_id, update_data):
        """Update a template"""
        update_data['updatedAt'] = datetime.utcnow()
        result = self.db.templates.update_one(
            {'_id': ObjectId(template_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0

    def delete_template(self, template_id):
        """Delete a template"""
        result = self.db.templates.delete_one({'_id': ObjectId(template_id)})
        return result.deleted_count > 0

    def create_product(self, product_data):
        """Create a new product"""
        product_data['createdAt'] = datetime.utcnow()
        product_data['updatedAt'] = datetime.utcnow()
        result = self.db.products.insert_one(product_data)
        return str(result.inserted_id)

    def get_product(self, product_id):
        """Get a product by ID"""
        try:
            return self.db.products.find_one({'_id': ObjectId(product_id)})
        except:
            return None

    def get_all_products(self, page=1, limit=10):
        """Get all products with pagination"""
        skip = (page - 1) * limit
        products = list(self.db.products.find().skip(skip).limit(limit))
        total = self.db.products.count_documents({})
        return products, total

    def update_product(self, product_id, update_data):
        """Update a product"""
        update_data['updatedAt'] = datetime.utcnow()
        result = self.db.products.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0

    def delete_product(self, product_id):
        """Delete a product"""
        result = self.db.products.delete_one({'_id': ObjectId(product_id)})
        return result.deleted_count > 0

# Global database manager instance
db_manager = None

def get_db_manager():
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def get_db():
    """Get database instance"""
    manager = get_db_manager()
    return manager.db
