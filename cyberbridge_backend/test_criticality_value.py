import requests
import json

# Test the products endpoint to see if criticality values are displayed correctly
def test_products_criticality_display():
    url = "http://localhost:8000/products"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Success! Response data:")
            print(json.dumps(data, indent=2))
            
            # Check if products have criticality values
            if isinstance(data, list):
                print(f"\nFound {len(data)} products")
                for i, product in enumerate(data):
                    print(f"Product {i+1}:")
                    print(f"  Name: {product.get('product_name')}")
                    print(f"  Criticality: {product.get('criticality', 'None')}")
                    print(f"  SBOM: {product.get('sbom', 'None')}")
                    print()
            else:
                print("Unexpected response format - not a list")
                
        elif response.status_code == 401:
            print("Authentication required - this is expected")
            print("The endpoint structure should be working, just needs auth")
        else:
            print(f"Error response:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("Could not connect to the server. Make sure the backend is running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_products_criticality_display()