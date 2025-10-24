#!/usr/bin/env python
"""
Script to add _id to variants in existing templates
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'mockup_db')

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB_NAME]
templates_collection = db['templates']

def fix_variant_ids():
    """Add _id to all variants that don't have one"""
    templates = templates_collection.find({})
    
    updated_count = 0
    for template in templates:
        needs_update = False
        variants = template.get('variants', [])
        
        for variant in variants:
            if '_id' not in variant:
                variant['_id'] = ObjectId()
                needs_update = True
        
        if needs_update:
            result = templates_collection.update_one(
                {'_id': template['_id']},
                {'$set': {'variants': variants}}
            )
            if result.modified_count > 0:
                updated_count += 1
                print(f"✅ Updated template: {template['name']} (ID: {template['_id']})")
    
    print(f"\n✅ Total templates updated: {updated_count}")

if __name__ == '__main__':
    print("=" * 60)
    print("Fix Variant IDs Script")
    print("=" * 60)
    print()
    
    try:
        fix_variant_ids()
        print("\n✅ Done!")
    except Exception as e:
        print(f"\n❌ Error: {e}")