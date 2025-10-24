"""
Fast version of the API using optimized image processing
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from bson import ObjectId
import traceback
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from db_utils import get_db
from models import Template, Variant
from image_utils_fast import composite_image_fast, FastImageCompositor
from s3_utils import upload_to_s3
from utils import generate_filename
import config

app = Flask(__name__)
CORS(app)

# Initialize database
db = get_db()
templates_collection = db['templates']

# Initialize fast compositor with thread pool
fast_compositor = FastImageCompositor(max_workers=8)  # Adjust based on CPU cores

# Helper function to serialize MongoDB documents
def serialize_doc(doc):
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        serialized = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                serialized[key] = serialize_doc(value)
            else:
                serialized[key] = value
        return serialized
    return doc

# Template Management APIs (same as app.py)

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get all templates with pagination"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        category = request.args.get('category')
        
        query = {}
        if category:
            query['category'] = category
        
        skip = (page - 1) * limit
        
        templates = list(templates_collection.find(query).skip(skip).limit(limit))
        total = templates_collection.count_documents(query)
        
        return jsonify({
            'success': True,
            'data': serialize_doc(templates),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get a single template by ID"""
    try:
        template = templates_collection.find_one({'_id': ObjectId(template_id)})
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
        
        return jsonify({
            'success': True,
            'data': serialize_doc(template)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/templates', methods=['POST'])
def create_template():
    """Create a new template"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'category', 'variants', 'dimensions', 'dpi']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Generate _id for each variant if not provided
        variants = data['variants']
        for variant in variants:
            if '_id' not in variant:
                variant['_id'] = ObjectId()
        
        template = {
            'name': data['name'],
            'description': data.get('description', ''),
            'category': data['category'],
            'dimensions': data['dimensions'],
            'dpi': data['dpi'],
            'variants': variants,
            'isActive': data.get('isActive', True),
            'tags': data.get('tags', []),
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        
        result = templates_collection.insert_one(template)
        template['_id'] = result.inserted_id
        
        return jsonify({
            'success': True,
            'data': serialize_doc(template)
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/templates/<template_id>', methods=['PUT'])
def update_template(template_id):
    """Update an existing template"""
    try:
        data = request.json
        
        # Generate _id for new variants if provided
        if 'variants' in data:
            for variant in data['variants']:
                if '_id' not in variant:
                    variant['_id'] = ObjectId()
                elif isinstance(variant['_id'], str):
                    variant['_id'] = ObjectId(variant['_id'])
        
        data['updatedAt'] = datetime.utcnow()
        
        result = templates_collection.update_one(
            {'_id': ObjectId(template_id)},
            {'$set': data}
        )
        
        if result.matched_count == 0:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
        
        template = templates_collection.find_one({'_id': ObjectId(template_id)})
        
        return jsonify({
            'success': True,
            'data': serialize_doc(template)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete a template"""
    try:
        result = templates_collection.delete_one({'_id': ObjectId(template_id)})
        
        if result.deleted_count == 0:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Template deleted successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Fast Image Compositing API

@app.route('/api/composite', methods=['POST'])
def composite_images():
    """Fast composite PNG images into mockup variants using parallel processing"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['templateId', 'sources', 'variantIds']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        template_id = data['templateId']
        sources = data['sources']
        variant_ids = data['variantIds']
        product_name_prefix = data.get('productNamePrefix', 'Design')
        options = data.get('options', {})
        
        # Get template
        template = templates_collection.find_one({'_id': ObjectId(template_id)})
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
        
        # Filter variants
        selected_variants = [v for v in template['variants'] if str(v['_id']) in variant_ids]
        if not selected_variants:
            return jsonify({'success': False, 'error': 'No valid variants found'}), 404
        
        results = []
        
        # Process each source image
        for idx, source in enumerate(sources):
            source_type = source.get('type', 'url')
            
            if source_type == 'url':
                source_url = source.get('imageUrl')
                if not source_url:
                    continue
                
                # Prepare batch processing data
                mockup_urls = [v['imageUrl'] for v in selected_variants]
                design_areas = [v['designArea'] for v in selected_variants]
                
                try:
                    # Batch composite all variants in parallel
                    composited_images = fast_compositor.composite_batch(
                        mockup_urls,
                        source_url,
                        design_areas,
                        options
                    )
                    
                    # Upload all images to S3 in parallel
                    def upload_single(args):
                        img_bytes, variant = args
                        file_name = generate_filename(product_name_prefix, variant['name'])
                        s3_url = upload_to_s3(img_bytes, file_name)
                        return {
                            'variantId': str(variant['_id']),
                            'variantName': variant['name'],
                            'sourceIndex': idx,
                            'imageUrl': s3_url,
                            'success': True
                        }
                    
                    with ThreadPoolExecutor(max_workers=8) as executor:
                        upload_results = list(executor.map(
                            upload_single,
                            zip(composited_images, selected_variants)
                        ))
                    
                    results.extend(upload_results)
                    
                except Exception as e:
                    # If batch processing fails, add error for all variants
                    for variant in selected_variants:
                        results.append({
                            'variantId': str(variant['_id']),
                            'variantName': variant['name'],
                            'sourceIndex': idx,
                            'error': str(e),
                            'success': False
                        })
        
        return jsonify({
            'success': True,
            'data': results,
            'total': len(results),
            'successful': len([r for r in results if r['success']])
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'version': 'fast',
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)