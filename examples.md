# API Usage Examples

This document provides practical examples of how to use the Mockup Image Compositing API.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```env
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=mockup_db
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-2
S3_BUCKET_NAME=your-bucket-name
```

3. Start the server:
```bash
python app.py
```

## Example 1: Create a Template

```bash
curl -X POST http://localhost:5000/api/templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mug White",
    "description": "White ceramic mug mockup",
    "category": "mug",
    "dimensions": {
      "width": 800,
      "height": 800
    },
    "dpi": 300,
    "variants": [
      {
        "name": "Main",
        "color": "#FFFFFF",
        "imageUrl": "https://funnytees-uploader.s3.us-east-2.amazonaws.com/variants/1761279795224-Img%20Main%202.jpg",
        "designArea": {
          "x": 1456.9867849595869,
          "y": 901.2734041883587,
          "width": 1153.4382422208462,
          "height": 1331.1562840983825,
          "rotation": 0,
          "opacity": 1
        }
      },
      {
        "name": "Image 1",
        "color": "#FFFFFF",
        "imageUrl": "https://funnytees-uploader.s3.us-east-2.amazonaws.com/variants/1761279833324-Img+1.jpg",
        "designArea": {
          "x": 2517.4545328056806,
          "y": 1592.9411520344509,
          "width": 1502.3123487205296,
          "height": 1733.7837870083667,
          "rotation": 0,
          "opacity": 1
        }
      }
    ],
    "isActive": true,
    "tags": ["mug", "white", "ceramic"]
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "_id": "68faff7e52b8e7b8980e5a81",
    "name": "Mug White",
    "description": "White ceramic mug mockup",
    "category": "mug",
    "dimensions": {
      "width": 800,
      "height": 800
    },
    "dpi": 300,
    "variants": [...],
    "isActive": true,
    "tags": ["mug", "white", "ceramic"],
    "createdAt": "2025-10-24T04:24:30.774Z",
    "updatedAt": "2025-10-24T04:24:30.774Z"
  }
}
```

## Example 2: Get All Templates

```bash
curl -X GET "http://localhost:5000/api/templates?page=1&limit=10&category=mug"
```

Response:
```json
{
  "success": true,
  "data": [
    {
      "_id": "68faff7e52b8e7b8980e5a81",
      "name": "Mug White",
      "category": "mug",
      ...
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "pages": 1
  }
}
```

## Example 3: Get Single Template

```bash
curl -X GET http://localhost:5000/api/templates/68faff7e52b8e7b8980e5a81
```

## Example 4: Update Template

```bash
curl -X PUT http://localhost:5000/api/templates/68faff7e52b8e7b8980e5a81 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mug White - Updated",
    "description": "Updated description"
  }'
```

## Example 5: Composite Images onto Mockup

This is the main feature - compositing a design PNG onto multiple mockup variants:

```bash
curl -X POST http://localhost:5000/api/composite \
  -H "Content-Type: application/json" \
  -d '{
    "templateId": "68faff7e52b8e7b8980e5a81",
    "sources": [
      {
        "type": "url",
        "imageUrl": "https://funnytees-uploader.s3.amazonaws.com/product-images/ecfa4320-bb3b-40a1-a7c3-efcd99067a1c/Freedom%20Signature%20Charlie%20Kirk%20T-Shirt_6.png"
      }
    ],
    "variantIds": [
      "68faff7e52b8e7b8980e5a82",
      "68faff7e52b8e7b8980e5a83",
      "68faffe552b8e7b8980e5a8c",
      "68faffe552b8e7b8980e5a8d"
    ],
    "productNamePrefix": "My Design",
    "options": {
      "centerDesign": true
    }
  }'
```

Response:
```json
{
  "success": true,
  "data": [
    {
      "variantId": "68faff7e52b8e7b8980e5a82",
      "variantName": "Main",
      "sourceIndex": 0,
      "imageUrl": "https://your-bucket.s3.us-east-2.amazonaws.com/composited-images/My_Design_Main_1.png",
      "success": true
    },
    {
      "variantId": "68faff7e52b8e7b8980e5a83",
      "variantName": "Image 1",
      "sourceIndex": 0,
      "imageUrl": "https://your-bucket.s3.us-east-2.amazonaws.com/composited-images/My_Design_Image_1_1.png",
      "success": true
    },
    {
      "variantId": "68faffe552b8e7b8980e5a8c",
      "variantName": "Image 2",
      "sourceIndex": 0,
      "imageUrl": "https://your-bucket.s3.us-east-2.amazonaws.com/composited-images/My_Design_Image_2_1.png",
      "success": true
    },
    {
      "variantId": "68faffe552b8e7b8980e5a8d",
      "variantName": "Image 3",
      "sourceIndex": 0,
      "imageUrl": "https://your-bucket.s3.us-east-2.amazonaws.com/composited-images/My_Design_Image_3_1.png",
      "success": true
    }
  ],
  "total": 4,
  "successful": 4
}
```

## Example 6: Delete Template

```bash
curl -X DELETE http://localhost:5000/api/templates/68faff7e52b8e7b8980e5a81
```

## Python Client Example

```python
import requests
import json

BASE_URL = "http://localhost:5000"

# Create a template
def create_template():
    template_data = {
        "name": "T-Shirt White",
        "description": "White t-shirt mockup",
        "category": "tshirt",
        "dimensions": {"width": 1000, "height": 1000},
        "dpi": 300,
        "variants": [
            {
                "name": "Front",
                "color": "#FFFFFF",
                "imageUrl": "https://example.com/tshirt-front.jpg",
                "designArea": {
                    "x": 300,
                    "y": 400,
                    "width": 400,
                    "height": 500,
                    "rotation": 0,
                    "opacity": 1
                }
            }
        ],
        "isActive": True,
        "tags": ["tshirt", "white"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/templates",
        json=template_data
    )
    return response.json()

# Composite images
def composite_images(template_id, variant_ids, design_url):
    composite_data = {
        "templateId": template_id,
        "sources": [
            {
                "type": "url",
                "imageUrl": design_url
            }
        ],
        "variantIds": variant_ids,
        "productNamePrefix": "Custom Design",
        "options": {
            "centerDesign": True
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/composite",
        json=composite_data
    )
    return response.json()

# Usage
if __name__ == "__main__":
    # Create template
    template_result = create_template()
    print("Template created:", template_result)
    
    # Composite images
    template_id = template_result['data']['_id']
    variant_ids = [v['_id'] for v in template_result['data']['variants']]
    design_url = "https://example.com/my-design.png"
    
    composite_result = composite_images(template_id, variant_ids, design_url)
    print("Composite result:", composite_result)
```

## JavaScript/Node.js Client Example

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:5000';

// Create a template
async function createTemplate() {
  const templateData = {
    name: 'T-Shirt White',
    description: 'White t-shirt mockup',
    category: 'tshirt',
    dimensions: { width: 1000, height: 1000 },
    dpi: 300,
    variants: [
      {
        name: 'Front',
        color: '#FFFFFF',
        imageUrl: 'https://example.com/tshirt-front.jpg',
        designArea: {
          x: 300,
          y: 400,
          width: 400,
          height: 500,
          rotation: 0,
          opacity: 1
        }
      }
    ],
    isActive: true,
    tags: ['tshirt', 'white']
  };
  
  const response = await axios.post(`${BASE_URL}/api/templates`, templateData);
  return response.data;
}

// Composite images
async function compositeImages(templateId, variantIds, designUrl) {
  const compositeData = {
    templateId: templateId,
    sources: [
      {
        type: 'url',
        imageUrl: designUrl
      }
    ],
    variantIds: variantIds,
    productNamePrefix: 'Custom Design',
    options: {
      centerDesign: true
    }
  };
  
  const response = await axios.post(`${BASE_URL}/api/composite`, compositeData);
  return response.data;
}

// Usage
(async () => {
  try {
    // Create template
    const templateResult = await createTemplate();
    console.log('Template created:', templateResult);
    
    // Composite images
    const templateId = templateResult.data._id;
    const variantIds = templateResult.data.variants.map(v => v._id);
    const designUrl = 'https://example.com/my-design.png';
    
    const compositeResult = await compositeImages(templateId, variantIds, designUrl);
    console.log('Composite result:', compositeResult);
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
})();
```

## Testing with Postman

1. Import the following collection into Postman
2. Set the base URL to `http://localhost:5000`
3. Create environment variables for `templateId` and `variantIds`

### Collection Structure:
- **Templates**
  - GET All Templates
  - GET Single Template
  - POST Create Template
  - PUT Update Template
  - DELETE Delete Template
- **Compositing**
  - POST Composite Images

## Common Issues and Solutions

### Issue: MongoDB Connection Failed
**Solution**: Ensure MongoDB is running and the connection string in `.env` is correct.

### Issue: S3 Upload Failed
**Solution**: Verify AWS credentials and bucket permissions in `.env`.

### Issue: Image Download Failed
**Solution**: Ensure the image URLs are accessible and the images are in supported formats (PNG, JPEG, etc.).

### Issue: Design Not Centered
**Solution**: Set `"centerDesign": true` in the options when calling the composite API.

## Performance Tips

1. **Use appropriate image sizes**: Larger images take longer to process
2. **Batch operations**: Process multiple variants in a single API call
3. **Cache templates**: Store frequently used templates in memory
4. **Optimize design areas**: Use precise coordinates to avoid unnecessary processing

## Security Considerations

1. **API Authentication**: Add authentication middleware for production use
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Input Validation**: Validate all input data before processing
4. **S3 Bucket Policies**: Configure proper S3 bucket policies and CORS settings