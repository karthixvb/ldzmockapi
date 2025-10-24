from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os

# MongoDB Connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'mockup_db')

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
templates_collection = db['templates']
products_collection = db['products']


class Template:
    """Template model for mockup templates"""
    
    @staticmethod
    def create(name, description, category, dimensions, dpi=300, tags=None):
        """Create a new template"""
        template = {
            'name': name,
            'description': description,
            'category': category,
            'dimensions': dimensions,
            'dpi': dpi,
            'tags': tags or [],
            'variants': [],
            'isActive': True,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        result = templates_collection.insert_one(template)
        return str(result.inserted_id)
    
    @staticmethod
    def get_by_id(template_id):
        """Get template by ID"""
        try:
            return templates_collection.find_one({'_id': ObjectId(template_id)})
        except:
            return None
    
    @staticmethod
    def get_all(page=1, limit=10):
        """Get all templates with pagination"""
        skip = (page - 1) * limit
        templates = list(templates_collection.find().skip(skip).limit(limit))
        total = templates_collection.count_documents({})
        
        return {
            'templates': templates,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }
    
    @staticmethod
    def update(template_id, update_data):
        """Update template"""
        try:
            update_data['updatedAt'] = datetime.utcnow()
            result = templates_collection.update_one(
                {'_id': ObjectId(template_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except:
            return False
    
    @staticmethod
    def delete(template_id):
        """Delete template"""
        try:
            result = templates_collection.delete_one({'_id': ObjectId(template_id)})
            return result.deleted_count > 0
        except:
            return False


class Variant:
    """Variant model for template variants"""
    
    @staticmethod
    def add_to_template(template_id, name, color, image_url, design_area):
        """Add variant to template"""
        try:
            variant = {
                '_id': ObjectId(),
                'name': name,
                'color': color,
                'imageUrl': image_url,
                'designArea': design_area,
            }
            result = templates_collection.update_one(
                {'_id': ObjectId(template_id)},
                {
                    '$push': {'variants': variant},
                    '$set': {'updatedAt': datetime.utcnow()}
                }
            )
            return str(variant['_id']) if result.modified_count > 0 else None
        except:
            return None
    
    @staticmethod
    def update_variant(template_id, variant_id, update_data):
        """Update variant in template"""
        try:
            result = templates_collection.update_one(
                {'_id': ObjectId(template_id), 'variants._id': ObjectId(variant_id)},
                {
                    '$set': {
                        'variants.$': {**update_data, '_id': ObjectId(variant_id)},
                        'updatedAt': datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except:
            return False
    
    @staticmethod
    def remove_from_template(template_id, variant_id):
        """Remove variant from template"""
        try:
            result = templates_collection.update_one(
                {'_id': ObjectId(template_id)},
                {
                    '$pull': {'variants': {'_id': ObjectId(variant_id)}},
                    '$set': {'updatedAt': datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except:
            return False


class Product:
    """Product model for composited products"""
    
    @staticmethod
    def create(template_id, variant_ids, product_name, image_url, source_image_url):
        """Create a new product from composited image"""
        product = {
            'templateId': template_id,
            'variantIds': variant_ids,
            'productName': product_name,
            'imageUrl': image_url,
            'sourceImageUrl': source_image_url,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        result = products_collection.insert_one(product)
        return str(result.inserted_id)
    
    @staticmethod
    def get_by_id(product_id):
        """Get product by ID"""
        try:
            return products_collection.find_one({'_id': ObjectId(product_id)})
        except:
            return None
    
    @staticmethod
    def get_all(page=1, limit=10):
        """Get all products with pagination"""
        skip = (page - 1) * limit
        products = list(products_collection.find().skip(skip).limit(limit))
        total = products_collection.count_documents({})
        
        return {
            'products': products,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }
    
    @staticmethod
    def delete(product_id):
        """Delete product"""
        try:
            result = products_collection.delete_one({'_id': ObjectId(product_id)})
            return result.deleted_count > 0
        except:
            return False
